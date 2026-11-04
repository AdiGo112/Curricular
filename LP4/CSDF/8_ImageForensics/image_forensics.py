# =========================================================
# MINI PROJECT 8
# Tool for Digital Forensics of Images
# =========================================================
#
# Checks performed on an image (evidence):
#
#   0. File information               -> size, modified /
#                                         accessed timestamps
#   1. Hashing (MD5, SHA-1, SHA-256)  -> proves integrity
#   2. File signature (magic bytes)    -> detects renamed /
#                                         disguised files
#   3. EXIF metadata                   -> camera, date, GPS,
#                                         editing software
#   4. Hidden appended data            -> bytes after the
#                                         end-of-image marker
#   5. LSB steganography               -> text hidden in the
#                                         least significant bits
#   6. Error Level Analysis (ELA)      -> regions that were
#                                         pasted / edited
#   7. EXIF thumbnail mismatch         -> embedded preview no
#                                         longer matches image
#   8. Timestamp consistency           -> capture / edit /
#                                         file times disagree
#   9. Copy-move (clone) detection     -> a region copied to
#                                         another place in the
#                                         same image
#  10. Corrupted JPEG data             -> invalid markers in
#                                         the compressed data
#  11. Embedded files                  -> ZIP/PDF/RAR/EXE/PNG
#                                         hidden INSIDE the file
#  12. Comments / text chunks          -> text hidden in JPEG
#                                         comments, PNG tEXt
#
# A text report and an ELA image are saved for each file,
# plus one HTML report (reports/report.html) for the case.
#
# =========================================================
# HOW TO RUN
# =========================================================
#
#   pip install pillow numpy
#
#   python image_forensics.py --demo          (creates sample
#                                              evidence and
#                                              analyses it)
#   python image_forensics.py photo.jpg       (your own file)
#   python image_forensics.py --ui            (drag-and-drop
#                                              page in the
#                                              browser)
#
# Output goes to the "reports" folder.
#
# =========================================================

import argparse
import base64
import datetime
import hashlib
import html
import io
import json
import os
import struct
import sys
import tempfile
import webbrowser
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer

import numpy as np
from PIL import ExifTags, Image, ImageChops, ImageDraw

# ---------------------------------------------------------
# Known file signatures (first bytes of the file)
# ---------------------------------------------------------
SIGNATURES = [
    (b"\xff\xd8\xff", "JPEG", [".jpg", ".jpeg"]),
    (b"\x89PNG\r\n\x1a\n", "PNG", [".png"]),
    (b"GIF87a", "GIF", [".gif"]),
    (b"GIF89a", "GIF", [".gif"]),
    (b"BM", "BMP", [".bmp"]),
    (b"PK\x03\x04", "ZIP", [".zip", ".docx", ".xlsx"]),
    (b"%PDF", "PDF", [".pdf"]),
    (b"MZ", "EXE", [".exe", ".dll"]),
]

# Signatures searched for INSIDE a file (long enough not to match by chance)
EMBEDDED_SIGNATURES = [
    (b"PK\x03\x04", "ZIP"),
    (b"%PDF-", "PDF"),
    (b"Rar!\x1a\x07", "RAR"),
    (b"7z\xbc\xaf\x27\x1c", "7-Zip"),
    (b"\x89PNG\r\n\x1a\n", "PNG"),
    (b"MZ\x90\x00", "EXE"),
]

# Bytes allowed after 0xFF inside JPEG compressed data: stuffed 00,
# restart markers D0-D7, end D9, and the tables/scans of progressive JPEGs.
JPEG_SCAN_OK = {0x00, 0xFF, 0xC4, 0xD9, 0xDA, 0xDB, 0xDD, *range(0xD0, 0xD8)}

EDITING_SOFTWARE = ["photoshop", "gimp", "paint.net", "lightroom", "snapseed", "picsart", "canva"]

ELA_QUALITY = 90       # quality used to re-save the image for ELA
ELA_BLOCK = 16         # ELA is compared block by block (pixels)
ELA_THRESHOLD = 3.0    # suspicious if smoothed |z-score| > 3
ELA_TEXTURE = 5        # ELA error is divided by (block texture + 5): busy texture naturally has high error
ELA_MIN_BLOCKS = 4     # fewer suspicious blocks than this = noise
# Tuned on 24 real photos (photos/, plus pasted copies of each):
# 0/24 false alarms, 18/24 pastes found. ponytail: re-tune if your camera's photos give false alarms.

THUMB_GRID = 32        # thumbnail and image compared on a 32-pixel-wide grid
THUMB_THRESHOLD = 25   # a grid cell differing by more than this = mismatch

CLONE_MAX_SIDE = 1024  # bigger photos are shrunk first to stay fast
                       # (ponytail: shrinking blurs exact copies, so clones in big photos are found less often)
CLONE_BLOCK = 16       # block size compared (pixels); a block starts at EVERY pixel
CLONE_NEIGHBOURS = 8   # each block is compared with its 8 nearest neighbours in sorted order
CLONE_TOLERANCE = 2.0  # max difference (grey levels) between two "identical" blocks: JPEG noise
CLONE_MIN_SHIFT = 24   # copies closer than this are ignored (neighbouring blocks look alike)
CLONE_MIN_MATCHES = 200  # this many blocks moved by the same offset = copy-move
CLONE_MIN_STD = 8      # flat blocks (sky, walls) are skipped, they match by accident
# Tuned on 24 real photos with a 128x96 region cloned in each:
# 0/24 false alarms, 19/24 clones found (the 5 missed were clones of flat sky/blur).

EXIF_DATE = "%Y:%m:%d %H:%M:%S"

UI_MAX_BYTES = 300 * 1024 * 1024   # largest upload the drag-and-drop page accepts


# =========================================================
# 1. HASHING
# =========================================================

def file_hashes(data):
    return {
        "MD5": hashlib.md5(data).hexdigest(),
        "SHA-1": hashlib.sha1(data).hexdigest(),
        "SHA-256": hashlib.sha256(data).hexdigest(),
    }


# =========================================================
# 2. FILE SIGNATURE CHECK
# =========================================================

def check_signature(path, data):
    ext = os.path.splitext(path)[1].lower()
    for magic, kind, exts in SIGNATURES:
        if data.startswith(magic):
            ok = ext in exts
            note = "matches extension" if ok else f"MISMATCH: extension '{ext}' but content is {kind}"
            return kind, ok, note
    return "Unknown", False, "Unknown file signature"


# =========================================================
# 3. EXIF METADATA
# =========================================================

def read_exif(img):
    exif = img.getexif()
    tags = dict(exif.items())
    tags.update(exif.get_ifd(0x8769))   # Exif sub-block: DateTimeOriginal, exposure, ...
    tags.pop(0x8769, None)
    tags.pop(0x8825, None)
    info = {ExifTags.TAGS.get(tag, tag): value for tag, value in tags.items()
            if not isinstance(value, bytes)}   # skip binary blobs like MakerNote

    gps = exif.get_ifd(0x8825)   # GPS block
    if gps:
        info["GPSInfo"] = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps.items()}
        info["GPS (lat, lon)"] = gps_decimal(info["GPSInfo"])

    findings = []
    software = str(info.get("Software", "")).lower()
    if any(s in software for s in EDITING_SOFTWARE):
        findings.append(f"Image was processed by editing software: {info['Software']}")
    if not info:
        findings.append("No EXIF metadata (it may have been stripped)")
    if "GPSInfo" in info:
        findings.append("GPS location present in metadata")
    return info, findings


def gps_decimal(gps):
    # EXIF stores degrees, minutes, seconds + N/S/E/W reference
    try:
        def deg(dms, ref):
            d, m, s = (float(x) for x in dms)
            v = d + m / 60 + s / 3600
            return -v if ref in ("S", "W") else v
        lat = deg(gps["GPSLatitude"], gps["GPSLatitudeRef"])
        lon = deg(gps["GPSLongitude"], gps["GPSLongitudeRef"])
        return f"{lat:.6f}, {lon:.6f}"
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return "present but could not be decoded"


# =========================================================
# 3b. EXIF THUMBNAIL MISMATCH
# =========================================================
#
# Cameras store a small preview JPEG inside the EXIF block.
# Many editors change the image but keep the old preview, so
# a preview that differs from the image is a tampering clue.
#

def jpeg_segments(data):
    # Walk the JPEG header: yields (marker, offset, payload) up to and
    # including the start-of-scan (0xDA), where the image data begins.
    i = 2
    while i + 4 <= len(data) and data[i] == 0xFF:
        marker = data[i + 1]
        length = int.from_bytes(data[i + 2:i + 4], "big")
        yield marker, i, data[i + 4:i + 2 + length]
        if marker == 0xDA:
            return
        i += 2 + length


def jpeg_scan_start(data):
    return next((off for m, off, _ in jpeg_segments(data) if m == 0xDA), -1)


def exif_thumbnail(data):
    for marker, _, seg in jpeg_segments(data):
        if marker == 0xE1 and seg.startswith(b"Exif"):
            start = seg.find(b"\xff\xd8\xff")
            end = seg.find(b"\xff\xd9", start)
            if start != -1 and end != -1:
                return seg[start:end + 2]
    return None


def check_thumbnail(data, img):
    thumb_bytes = exif_thumbnail(data)
    if not thumb_bytes:
        return "no embedded thumbnail", False
    try:
        thumb = Image.open(io.BytesIO(thumb_bytes)).convert("L")
    except Exception:
        return "embedded thumbnail is unreadable", True

    if abs(thumb.width / thumb.height - img.width / img.height) > 0.05:
        return (f"aspect ratio differs ({thumb.width}x{thumb.height} preview vs "
                f"{img.width}x{img.height} image), image may be cropped"), True

    h = max(1, round(THUMB_GRID * img.height / img.width))
    a = np.asarray(thumb.resize((THUMB_GRID, h), Image.BOX), dtype=np.int16)
    b = np.asarray(img.convert("L").resize((THUMB_GRID, h), Image.BOX), dtype=np.int16)
    worst = int(np.abs(a - b).max())
    if worst > THUMB_THRESHOLD:
        return f"MISMATCH: preview differs from image (max cell difference {worst})", True
    return f"matches image (max cell difference {worst})", False


# =========================================================
# 3c. TIMESTAMP CONSISTENCY
# =========================================================

def check_timestamps(exif, mtime):
    findings = []
    dates = {}
    for tag in ("DateTimeOriginal", "DateTime"):
        if tag in exif:
            try:
                dates[tag] = datetime.datetime.strptime(str(exif[tag]).strip("\x00 "), EXIF_DATE)
            except ValueError:
                findings.append(f"{tag} has an invalid format: {exif[tag]}")

    taken, changed = dates.get("DateTimeOriginal"), dates.get("DateTime")
    file_time = datetime.datetime.fromtimestamp(mtime)
    now = datetime.datetime.now()

    if taken and changed and changed < taken:
        findings.append(f"EXIF modify time {changed} is BEFORE capture time {taken}")
    elif taken and changed and (changed - taken).total_seconds() > 60:
        findings.append(f"Modified after capture: taken {taken}, changed {changed}")
    for tag, value in dates.items():
        if value > now:
            findings.append(f"{tag} {value} is in the future")
        elif value > file_time:
            findings.append(f"{tag} {value} is later than the file's own modified time {file_time:%Y-%m-%d %H:%M:%S}")
    return findings


# =========================================================
# 4. HIDDEN DATA AFTER END OF IMAGE
# =========================================================

def appended_data(kind, data):
    if kind == "JPEG":
        sos = jpeg_scan_start(data)
        end = data.rfind(b"\xff\xd9", max(sos, 0))   # not the EXIF preview's end marker
        end = -1 if sos == -1 or end == -1 else end + 2
    elif kind == "PNG":
        end = data.rfind(b"IEND")
        end = -1 if end == -1 else end + 8      # 'IEND' + 4-byte CRC
    else:
        return 0, b""
    if end == -1:
        return -1, b""                          # end marker missing
    if end >= len(data):
        return 0, b""
    return len(data) - end, data[end:]


def corrupt_scan_markers(data):
    # Inside JPEG compressed data a 0xFF byte may only be followed by a
    # few known values. Random damage (bit rot, bad sectors, partial
    # overwrite) creates other values almost immediately.
    # ponytail: DHT tables between progressive scans could hold FF bytes too; not seen in practice
    sos, end = jpeg_scan_start(data), data.rfind(b"\xff\xd9")
    if sos == -1:
        return []
    end = len(data) if end < sos else end
    bad, i = [], data.find(b"\xff", sos + 2)
    while 0 <= i < end - 1:
        if data[i + 1] not in JPEG_SCAN_OK:
            bad.append(i)
        i = data.find(b"\xff", i + 1)
    return bad


def embedded_files(data, limit):
    # File signatures found inside the file (not at offset 0, not in the appended part)
    found = []
    for magic, kind in EMBEDDED_SIGNATURES:
        i = data.find(magic, 1)
        while i != -1 and i < limit:
            found.append((i, kind))
            i = data.find(magic, i + 1)
    return sorted(found)


def text_comments(data, img):
    texts = []
    if img is None or img.format == "JPEG":
        texts += [seg.decode("latin-1") for m, _, seg in jpeg_segments(data) if m == 0xFE]
    if img is not None and img.format == "PNG":
        texts += [f"{k}: {v}" for k, v in img.text.items()]
    return texts


def describe_blob(blob):
    for magic, kind, _ in SIGNATURES:
        if blob.startswith(magic):
            return kind
    return "text" if blob[:64].isascii() else "binary"


# =========================================================
# 5. LSB STEGANOGRAPHY
# =========================================================
#
# Text hidden by putting each bit of the message into the
# lowest bit of the red channel, ending with a 0 byte.
#

def lsb_hide(img, message):
    arr = np.array(img.convert("RGB"))
    bits = np.unpackbits(np.frombuffer(message.encode() + b"\x00", dtype=np.uint8))
    red = arr[:, :, 0].flatten()
    if len(bits) > len(red):
        raise ValueError("Message too long for this image")
    red[: len(bits)] = (red[: len(bits)] & 0xFE) | bits
    arr[:, :, 0] = red.reshape(arr.shape[:2])
    return Image.fromarray(arr)


def lsb_extract(img, max_chars=500):
    red = np.array(img.convert("RGB"))[:, :, 0].flatten()
    raw = np.packbits(red[: max_chars * 8] & 1).tobytes()
    text = raw.split(b"\x00", 1)[0]
    # Only report it if it looks like real readable text
    if len(text) >= 4 and all(32 <= c < 127 for c in text) and b"\x00" in raw:
        return text.decode()
    return None


# =========================================================
# 6. ERROR LEVEL ANALYSIS (ELA)
# =========================================================
#
# Re-save the JPEG at a known quality and compare. Areas that
# were pasted in later have a different compression history,
# so their error level stands out from the rest of the image.
#

def error_level_analysis(img, ela_path):
    rgb = img.convert("RGB")
    buf = io.BytesIO()
    rgb.save(buf, "JPEG", quality=ELA_QUALITY)
    resaved = Image.open(buf)

    diff = np.asarray(ImageChops.difference(rgb, resaved), dtype=np.float32).mean(axis=2)

    # save a brightened ELA image for the report
    scale = 255.0 / max(diff.max(), 1)
    Image.fromarray((diff * scale).astype(np.uint8)).save(ela_path)

    h, w = diff.shape
    h, w = h - h % ELA_BLOCK, w - w % ELA_BLOCK

    def per_block(a):
        return a[:h, :w].reshape(h // ELA_BLOCK, ELA_BLOCK, w // ELA_BLOCK, ELA_BLOCK)

    blocks = per_block(diff).mean(axis=(1, 3))

    # Detailed areas (leaves, tiles, text) always have a high error
    # level, smooth areas (sky) a low one. Dividing by the block's
    # texture removes that, so only a different compression
    # history stands out.
    texture = per_block(np.asarray(rgb.convert("L"), dtype=np.float32)).std(axis=(1, 3))
    relative = blocks / (texture + ELA_TEXTURE)

    # A pasted region can be HIGHER or LOWER than the rest
    # (e.g. a smoother, more compressed patch), so check both.
    z = (relative - relative.mean()) / max(relative.std(), 1e-6)

    # Average every block with its 8 neighbours: random noisy
    # blocks cancel out, a real pasted region stays strong.
    p = np.pad(z, 1, mode="edge")
    z = sum(p[i:i + z.shape[0], j:j + z.shape[1]] for i in range(3) for j in range(3)) / 9

    rows, cols = np.where(np.abs(z) > ELA_THRESHOLD)
    if len(rows) < ELA_MIN_BLOCKS:
        rows, cols = rows[:0], cols[:0]
    pct = len(rows) / z.size * 100
    if len(rows) == 0:
        level = "LOW - uniform error levels; no obvious tampering"
    elif pct <= 5:
        level = "MEDIUM - localised regions differ (possible paste/clone); inspect the ELA image"
    else:
        level = "HIGH - large regions differ; manual inspection advised"
    stats = {
        "Max error difference": int(diff.max()),
        "Average block error": round(float(blocks.mean()), 3),
        "Suspicious blocks": f"{len(rows)} of {z.size} ({pct:.2f}%)",
        "Tampering suspicion": level,
    }
    if len(rows) == 0:
        return None, stats
    return (int(cols.min() * ELA_BLOCK), int(rows.min() * ELA_BLOCK),
            int((cols.max() + 1) * ELA_BLOCK), int((rows.max() + 1) * ELA_BLOCK), len(rows)), stats


# =========================================================
# 7. COPY-MOVE (CLONE) DETECTION
# =========================================================
#
# A 16x16 block starts at EVERY pixel, so a copied region always
# has an exact twin (a copy can be moved by any number of pixels).
# Each block is described by its 4x4 grid of average brightness,
# the blocks are sorted so similar ones sit next to each other,
# and each is compared with its nearest neighbours. A real clone
# shows hundreds of matching pairs moved by the SAME offset;
# repeated textures give scattered offsets.
#

def copy_move(img):
    gray = img.convert("L")
    scale = min(1.0, CLONE_MAX_SIDE / max(gray.size))
    if scale < 1:
        gray = gray.resize((round(gray.width * scale), round(gray.height * scale)), Image.BOX)
    a = np.asarray(gray, dtype=np.float32)
    B = CLONE_BLOCK
    if min(a.shape) < 2 * B:
        return None

    # cell[y, x] = average of the 4x4 pixels starting at (x, y), via a summed-area table
    ii = np.pad(a.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    cell = (ii[4:, 4:] - ii[:-4, 4:] - ii[4:, :-4] + ii[:-4, :-4]) / 16
    ys, xs = np.mgrid[0:a.shape[0] - B + 1, 0:a.shape[1] - B + 1]
    ys, xs = ys.ravel(), xs.ravel()
    feats = np.stack([cell[ys + 4 * i, xs + 4 * j] for i in range(4) for j in range(4)], axis=1)

    keep = feats.std(axis=1) >= CLONE_MIN_STD
    feats, ys, xs = feats[keep], ys[keep], xs[keep]
    if len(ys) < 2:
        return None

    # sort along the direction the blocks differ most (first principal component)
    centred = feats - feats.mean(axis=0)
    direction = np.linalg.svd(centred[:: max(1, len(centred) // 5000)], full_matrices=False)[2][0]
    order = np.argsort(centred @ direction)
    feats, ys, xs = feats[order], ys[order], xs[order]

    pairs = []
    for k in range(1, CLONE_NEIGHBOURS + 1):
        close = np.abs(feats[k:] - feats[:-k]).max(axis=1) < CLONE_TOLERANCE
        dx, dy = xs[k:] - xs[:-k], ys[k:] - ys[:-k]
        flip = (dy < 0) | ((dy == 0) & (dx < 0))      # same shift either direction
        dx, dy = np.where(flip, -dx, dx), np.where(flip, -dy, dy)
        i = np.where(close & (np.hypot(dx, dy) >= CLONE_MIN_SHIFT))[0]
        src_x, src_y = np.where(flip, xs[k:], xs[:-k])[i], np.where(flip, ys[k:], ys[:-k])[i]
        pairs.append(np.stack([dx[i], dy[i], src_x, src_y], axis=1))
    pairs = np.concatenate(pairs)
    if len(pairs) == 0:
        return None

    shifts, counts = np.unique(pairs[:, :2], axis=0, return_counts=True)
    best = counts.argmax()
    if counts[best] < CLONE_MIN_MATCHES:
        return None
    sx, sy = shifts[best]
    src = pairs[(pairs[:, 0] == sx) & (pairs[:, 1] == sy)][:, 2:]
    dst = src + [sx, sy]

    def box(p):
        x1, y1 = p.min(axis=0)
        x2, y2 = p.max(axis=0) + B
        return tuple(int(v / scale) for v in (x1, y1, x2, y2))

    return box(src), box(dst), int(counts[best])


# =========================================================
# ANALYSE ONE FILE
# =========================================================

def run_checks(path, out_dir):
    with open(path, "rb") as f:
        data = f.read()

    name = os.path.basename(path)
    st = os.stat(path)
    ts = lambda t: datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")
    lines = ["=" * 64, f" IMAGE FORENSIC REPORT: {name}",
             f" Generated on: {ts(datetime.datetime.now().timestamp())}", "=" * 64,
             f"File size : {len(data)} bytes",
             f"Modified  : {ts(st.st_mtime)}",
             f"Accessed  : {ts(st.st_atime)}"]
    suspicious = []
    extras = {"path": path}

    for algo, value in file_hashes(data).items():
        lines.append(f"{algo:8}  : {value}")

    kind, ok, note = check_signature(path, data)
    lines.append(f"Signature : {kind} ({note})")
    if not ok:
        suspicious.append(note)

    size, blob = appended_data(kind, data)
    if size == -1:
        lines.append(f"Appended  : {kind} end marker not found (file may be corrupted/truncated)")
    elif size:
        msg = f"{size} bytes of hidden {describe_blob(blob)} data after end-of-image marker"
        lines.append(f"Appended  : {msg}")
        suspicious.append(msg)
    else:
        lines.append("Appended  : none")
    if size == -1:
        suspicious.append(f"{kind} end marker missing: file is truncated or corrupted")

    inside = embedded_files(data, len(data) - max(size, 0))
    if inside:
        kinds = ", ".join(f"{k} at byte {o}" for o, k in inside[:5])
        msg = f"Embedded file signature(s) inside the image: {kinds}"
        lines.append(f"Embedded  : {msg}")
        suspicious.append(msg)
    else:
        lines.append("Embedded  : none")

    if kind == "JPEG":
        bad = corrupt_scan_markers(data)
        if bad:
            msg = f"Corrupted image data: {len(bad)} invalid marker(s), first at byte {bad[0]}"
            lines.append(f"Integrity : {msg}")
            suspicious.append(msg)
        else:
            lines.append("Integrity : compressed data structure OK")

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as e:
        msg = f"Image cannot be decoded ({str(e).split(' <')[0]})"
        lines.append(f"Image     : {msg}")
        suspicious.append(msg)
        return lines, suspicious, extras

    lines.append(f"Format    : {img.format}, {img.size[0]}x{img.size[1]}, mode {img.mode}")

    exif, exif_findings = read_exif(img)
    lines.append("\n--- EXIF metadata ---")
    lines += [f"{k}: {v}" for k, v in exif.items()] or ["(none)"]
    suspicious += [f for f in exif_findings if "No EXIF" not in f]
    lines += [f"NOTE: {f}" for f in exif_findings]

    lines.append("\n--- Comments / text chunks ---")
    texts = text_comments(data, img)
    lines += [f"Text: {t[:200]}" for t in texts] or ["none"]
    if texts:   # ponytail: any comment is flagged for review, even harmless ones like "CREATOR: gd-jpeg"
        suspicious.append(f"Text hidden in comment/text chunk: {texts[0][:80]}")

    lines.append("\n--- Timestamp consistency ---")
    times = check_timestamps(exif, st.st_mtime)
    lines += times or ["Capture, edit and file times are consistent (or not recorded)"]
    suspicious += times

    lines.append("\n--- EXIF thumbnail ---")
    if img.format == "JPEG":
        msg, bad = check_thumbnail(data, img)
        lines.append(f"Thumbnail : {msg}")
        if bad:
            suspicious.append(f"EXIF thumbnail {msg}")
    else:
        lines.append("Skipped (EXIF thumbnails are a JPEG feature)")

    hidden = lsb_extract(img)
    lines.append("\n--- LSB steganography ---")
    if hidden:
        lines.append(f"Hidden message found: \"{hidden}\"")
        suspicious.append("LSB hidden message present")
    else:
        lines.append("No hidden LSB text found")

    lines.append("\n--- Error Level Analysis ---")
    if img.format == "JPEG":
        ela_path = os.path.join(out_dir, os.path.splitext(name)[0] + "_ELA.png")
        region, stats = error_level_analysis(img, ela_path)
        extras["ela"], extras["ela_box"] = ela_path, region
        lines.append(f"ELA image saved: {ela_path}")
        lines += [f"{k:22}: {v}" for k, v in stats.items()]
        if region:
            x1, y1, x2, y2, n = region
            msg = f"Possible edited region at ({x1},{y1})-({x2},{y2}), {n} blocks"
            lines.append(msg)
            suspicious.append(msg)
        else:
            lines.append("Uniform error level, no edited region detected")
    else:
        lines.append("Skipped (ELA applies to JPEG only)")

    lines.append("\n--- Copy-move (clone) detection ---")
    clone = copy_move(img)
    if clone:
        src, dst, n = clone
        msg = f"Copy-move: regions {src} and {dst} are identical ({n} matching blocks)"
        lines.append(msg)
        suspicious.append(msg)
        extras["clone_boxes"] = [src, dst]
    else:
        lines.append("No duplicated regions found")
    return lines, suspicious, extras


def analyse(path, out_dir):
    lines, suspicious, extras = run_checks(path, out_dir)
    lines.append("\n--- VERDICT ---")
    if suspicious:
        lines.append("SUSPICIOUS:")
        lines += [f"  - {s}" for s in suspicious]
    else:
        lines.append("No signs of tampering found")
    return lines, suspicious, extras


# =========================================================
# HTML CASE REPORT
# =========================================================

def img_tag(pil_img, boxes=(), colour="red"):
    pil_img = pil_img.convert("RGB")
    draw = ImageDraw.Draw(pil_img)
    for b in boxes:
        draw.rectangle(b, outline=colour, width=max(2, pil_img.width // 200))
    pil_img.thumbnail((520, 520))
    buf = io.BytesIO()
    pil_img.save(buf, "PNG")
    return f'<img src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}" alt="">'


def write_html(results, out_path):
    rows, sections = [], []
    for name, (lines, sus, extras) in results.items():
        status = "SUSPICIOUS" if sus else "CLEAN"
        anchor = html.escape(name, quote=True)
        rows.append(f'<tr><td><a href="#{anchor}">{html.escape(name)}</a></td>'
                    f'<td class="{status.lower()}">{status}</td><td>{len(sus)}</td></tr>')
        pics = []
        try:
            pics.append("<figure>" + img_tag(Image.open(extras["path"]), extras.get("clone_boxes", []))
                        + "<figcaption>Evidence (cloned regions boxed in red)</figcaption></figure>")
        except Exception:
            pass                                 # not an image: report text only
        if extras.get("ela"):
            box = [extras["ela_box"][:4]] if extras.get("ela_box") else []
            pics.append("<figure>" + img_tag(Image.open(extras["ela"]), box, "yellow")
                        + "<figcaption>ELA (suspected edit boxed in yellow)</figcaption></figure>")
        findings = "".join(f"<li>{html.escape(s)}</li>" for s in sus) or "<li>No signs of tampering found</li>"
        report = html.escape("\n".join(lines))
        sections.append(f'<section id="{anchor}"><h2>{html.escape(name)} '
                        f'<span class="{status.lower()}">{status}</span></h2>'
                        f'<div class="pics">{"".join(pics)}</div><h3>Findings</h3><ul>{findings}</ul>'
                        f'<details><summary>Full report</summary><pre>{report}</pre></details></section>')

    page = f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Image Forensic Case Report</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:1100px;margin:auto;padding:16px;background:#fafafa;color:#222}}
table{{border-collapse:collapse;width:100%}} td,th{{border:1px solid #ccc;padding:6px 10px;text-align:left}}
.suspicious{{color:#b00020;font-weight:bold}} .clean{{color:#1b7f3a;font-weight:bold}}
section{{background:#fff;border:1px solid #ddd;border-radius:8px;padding:12px 16px;margin:16px 0}}
.pics{{display:flex;flex-wrap:wrap;gap:12px}} figure{{margin:0}} img{{max-width:100%;border:1px solid #ccc}}
figcaption{{font-size:13px;color:#666}} pre{{background:#f3f3f3;padding:10px;overflow-x:auto;font-size:12px}}
</style></head><body>
<h1>Image Forensic Case Report</h1>
<p>Generated on {datetime.datetime.now():%Y-%m-%d %H:%M:%S}, {len(results)} file(s) examined.</p>
<table><tr><th>File</th><th>Status</th><th>Findings</th></tr>{"".join(rows)}</table>
{"".join(sections)}
</body></html>
"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)


# =========================================================
# DRAG-AND-DROP WEB UI  (python image_forensics.py --ui)
# =========================================================
#
# A local page served by Python's own web server. Dropped files
# are written to a temporary folder (exact bytes, so the hashes
# are those of the evidence), analysed with analyse(), and the
# HTML case report is shown on the page. Only 127.0.0.1 can
# connect; nothing leaves the machine.
#

UPLOAD_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Image Forensics Tool</title>
<style>
body{font-family:system-ui,sans-serif;max-width:1100px;margin:auto;padding:16px;background:#fafafa;color:#222}
#zone{display:block;border:3px dashed #999;border-radius:12px;padding:40px 16px;text-align:center;
      background:#fff;cursor:pointer;font-size:18px}
#zone.over,#zone:focus-within{border-color:#1565c0;background:#e3f2fd}
#zone small{display:block;color:#666;font-size:14px;margin-top:6px}
#file{position:absolute;opacity:0;width:1px;height:1px}
ul{padding-left:20px} li{margin:2px 0}
.bar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:12px 0}
button,a.btn{font-size:16px;padding:8px 18px;border-radius:6px;border:1px solid #1565c0;background:#1565c0;
             color:#fff;cursor:pointer;text-decoration:none}
button.secondary{background:#fff;color:#1565c0}
button:disabled{opacity:.5;cursor:default}
#status{color:#555}
iframe{width:100%;border:0;min-height:200px}
</style></head><body>
<h1>Image Forensics Tool</h1>
<label id="zone">Drop images / files here, or click to choose
  <small>Checks: hashes, file signature, EXIF, timestamps, thumbnail, hidden data, LSB stego, ELA, copy-move</small>
  <input id="file" type="file" multiple>
</label>
<ul id="list"></ul>
<div class="bar">
  <button id="go" disabled>Analyse</button>
  <button id="clear" class="secondary" disabled>Clear</button>
  <a id="save" class="btn" hidden download="forensic_report.html">Download report</a>
  <span id="status" role="status"></span>
</div>
<iframe id="out" title="Forensic report"></iframe>
<script>
const $ = id => document.getElementById(id);
let files = [];
const kb = n => n < 1048576 ? (n / 1024).toFixed(1) + " KB" : (n / 1048576).toFixed(2) + " MB";
function render() {
  $("list").innerHTML = "";
  for (const f of files) {
    const li = document.createElement("li");
    li.textContent = f.name + " (" + kb(f.size) + ")";
    $("list").appendChild(li);
  }
  $("go").disabled = $("clear").disabled = !files.length;
}
function add(list) { files.push(...list); render(); }
addEventListener("dragover", e => e.preventDefault());      // stop the browser opening the file
addEventListener("drop", e => e.preventDefault());
$("zone").addEventListener("dragover", () => $("zone").classList.add("over"));
$("zone").addEventListener("dragleave", () => $("zone").classList.remove("over"));
$("zone").addEventListener("drop", e => { $("zone").classList.remove("over"); add(e.dataTransfer.files); });
$("file").addEventListener("change", e => { add(e.target.files); e.target.value = ""; });
$("clear").addEventListener("click", () => { files = []; render(); $("status").textContent = ""; });
const b64 = f => new Promise((ok, bad) => {
  const r = new FileReader();
  r.onload = () => ok(r.result.split(",")[1]);
  r.onerror = () => bad(r.error);
  r.readAsDataURL(f);
});
$("go").addEventListener("click", async () => {
  $("go").disabled = true;
  $("status").textContent = "Analysing " + files.length + " file(s)...";
  try {
    const body = {files: await Promise.all(files.map(async f =>
      ({name: f.name, modified: f.lastModified, data: await b64(f)})))};
    const res = await fetch("/analyse", {method: "POST", body: JSON.stringify(body),
                                         headers: {"Content-Type": "application/json"}});
    if (!res.ok) throw new Error(res.status + " " + res.statusText);
    const page = await res.text();
    $("out").srcdoc = page;
    $("save").href = URL.createObjectURL(new Blob([page], {type: "text/html"}));
    $("save").hidden = false;
    $("status").textContent = "Done.";
  } catch (err) {
    $("status").textContent = "Failed: " + err.message;
  }
  $("go").disabled = false;
});
$("out").addEventListener("load", () => {
  const doc = $("out").contentDocument;
  if (doc) $("out").style.height = doc.documentElement.scrollHeight + 20 + "px";
});
</script>
</body></html>
"""


class UIHandler(BaseHTTPRequestHandler):
    def _send(self, body, ctype="text/html; charset=utf-8"):
        body = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != "/":
            return self.send_error(404)
        self._send(UPLOAD_PAGE)

    def do_POST(self):
        if self.path != "/analyse":
            return self.send_error(404)
        size = int(self.headers.get("Content-Length", 0))
        if size > UI_MAX_BYTES:
            return self.send_error(413, "Upload too large")
        try:
            uploads = json.loads(self.rfile.read(size))["files"]
            uploads = [(u["name"], u.get("modified"), base64.b64decode(u["data"], validate=True))
                       for u in uploads]
        except (ValueError, KeyError, TypeError):
            return self.send_error(400, "Bad upload")

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            evidence = os.path.join(tmp, "evidence")
            os.makedirs(evidence)
            results = {}
            for name, modified, data in uploads:
                name = os.path.basename(str(name))
                if name in ("", ".", ".."):
                    name = "unnamed"
                while name in results:                   # two files with the same name
                    name = "_" + name
                path = os.path.join(evidence, name)
                with open(path, "wb") as f:
                    f.write(data)
                if isinstance(modified, (int, float)):   # keep the file's real modified time
                    os.utime(path, (modified / 1000, modified / 1000))
                results[name] = analyse(path, tmp)
            report = os.path.join(tmp, "report.html")
            write_html(results, report)
            with open(report, encoding="utf-8") as f:
                page = f.read()
        self._send(page)


def run_ui(port):
    server = HTTPServer(("127.0.0.1", port), UIHandler)
    url = f"http://127.0.0.1:{port}/"
    print(f"Image forensics UI running at {url}  (Ctrl+C to stop)")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


# =========================================================
# DEMO: create sample evidence files
# =========================================================

PHOTOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "photos")   # real photos, see photos/CREDITS.md


def photo(name):
    return Image.open(os.path.join(PHOTOS, name + ".jpg")).convert("RGB")


def exif_bytes(img, software=None, changed="2026:10:15 09:30:00", gps=None):
    # Camera-style EXIF with an embedded preview of `img`.
    # Pillow cannot write the preview (IFD1), so it is linked in by hand.
    exif = Image.Exif()
    exif[0x010F] = "Canon"                       # Make
    exif[0x0110] = "Canon EOS 1500D"             # Model
    exif[0x0132] = changed                       # DateTime (last change)
    if software:
        exif[0x0131] = software                  # Software
    exif.get_ifd(0x8769)[0x9003] = "2026:10:15 09:30:00"   # DateTimeOriginal (capture)
    if gps:
        exif.get_ifd(0x8825).update(gps)

    preview = img.convert("RGB")
    preview.thumbnail((160, 160))
    buf = io.BytesIO()
    preview.save(buf, "JPEG", quality=75)
    thumb = buf.getvalue()

    raw = bytearray(exif.tobytes())              # b"Exif\0\0" + TIFF data
    tiff = 6
    e = "<" if raw[tiff:tiff + 2] == b"II" else ">"
    ifd0 = struct.unpack(e + "I", raw[tiff + 4:tiff + 8])[0]
    n = struct.unpack(e + "H", raw[tiff + ifd0:tiff + ifd0 + 2])[0]
    next_ptr = tiff + ifd0 + 2 + 12 * n          # IFD0's "next IFD" pointer
    if len(raw) % 2:
        raw += b"\x00"
    ifd1 = len(raw) - tiff
    raw[next_ptr:next_ptr + 4] = struct.pack(e + "I", ifd1)
    data_at = ifd1 + 2 + 3 * 12 + 4
    raw += struct.pack(e + "H", 3)
    raw += struct.pack(e + "HHIH", 0x0103, 3, 1, 6) + b"\x00\x00"   # Compression = JPEG
    raw += struct.pack(e + "HHII", 0x0201, 4, 1, data_at)            # preview offset
    raw += struct.pack(e + "HHII", 0x0202, 4, 1, len(thumb))         # preview length
    raw += struct.pack(e + "I", 0) + thumb
    return bytes(raw)


def camera_jpeg(img, preview=None, comment=None, **exif_kw):
    # JPEG bytes as a camera would save them: EXIF + embedded preview.
    # `preview` lets a sample keep a stale preview of the unedited photo.
    buf = io.BytesIO()
    extra = {"comment": comment} if comment else {}
    img.save(buf, "JPEG", quality=95, exif=exif_bytes(preview or img, **exif_kw), **extra)
    return buf.getvalue()


def make_demo(folder):
    os.makedirs(folder, exist_ok=True)

    def write(name, data):
        with open(os.path.join(folder, name), "wb") as f:
            f.write(data)

    # 1. Original camera photo (preview matches, times consistent)
    write("original.jpg", camera_jpeg(photo("forest_coast")))

    # 2. Tampered: bicycle cut from another photo, scaled down and pasted
    #    onto the street, saved by Photoshop a week later. The editor kept
    #    the OLD preview.
    street = photo("street")
    buf = io.BytesIO()
    bike = photo("bicycle").crop((400, 330, 820, 570)).resize((210, 120), Image.LANCZOS)
    bike.save(buf, "JPEG", quality=70)            # different compression history
    edited = street.copy()
    edited.paste(Image.open(buf), (100, 420))
    write("tampered.jpg", camera_jpeg(edited, preview=street, software="Adobe Photoshop 25.0",
                                      changed="2026:10:22 09:30:00"))

    # 3. Cloned: a flower cluster copied into the sky of the SAME photo.
    #    Careful forger: fresh preview, original EXIF kept.
    flowers = photo("flowers")
    flowers.paste(flowers.crop((340, 120, 530, 300)), (700, 40))
    write("cloned.jpg", camera_jpeg(flowers))

    # 4. Secret ZIP file appended after the JPEG
    write("holiday.jpg", camera_jpeg(photo("beach")) + b"PK\x03\x04" + b"secret_plans.txt" + b"\x00" * 40)

    # 5. Message hidden with LSB steganography (PNG keeps bits exactly)
    lsb_hide(photo("mountains"), "Meet at dock 7, 11pm").save(os.path.join(folder, "stego.png"))

    # 6. PNG image disguised as a text file
    photo("sea_cliff").resize((240, 160)).save(os.path.join(folder, "notes.txt"), "PNG")

    # ---- Corrupted files ----
    # 7. Download cut off half way: no end marker
    jpeg = camera_jpeg(photo("waterfall"))
    write("truncated.jpg", jpeg[: len(jpeg) // 2])

    # 8. First bytes wiped: file signature destroyed
    write("corrupted_header.jpg", b"\x00" * 16 + camera_jpeg(photo("valley"))[16:])

    # 9. Bad sector / bit rot: random bytes in the middle of the image data
    damaged = bytearray(camera_jpeg(photo("cafe")))
    mid = jpeg_scan_start(damaged) + (len(damaged) - jpeg_scan_start(damaged)) // 2
    damaged[mid:mid + 400] = np.random.default_rng(8).integers(0, 256, 400, dtype=np.uint8).tobytes()
    write("broken_data.jpg", bytes(damaged))

    # ---- Hidden data ----
    # 10. Secret text in a JPEG comment segment
    write("comment.jpg", camera_jpeg(photo("laptop"), comment=b"password for the drive: tiger@123"))

    # 11. Text appended after the PNG end chunk (IEND)
    buf = io.BytesIO()
    photo("clouds").save(buf, "PNG")
    write("after_iend.png", buf.getvalue() + b"FLAG{hidden_after_iend}")

    # 12. Real ZIP hidden INSIDE the JPEG header (APP15 segment), not at the end
    zbuf = io.BytesIO()
    with zipfile.ZipFile(zbuf, "w") as z:
        z.writestr("accounts.txt", "acct 4402-1187, pin 0420")
    zdata = zbuf.getvalue()
    jpeg = camera_jpeg(photo("path"))
    write("embedded_zip.jpg", jpeg[:2] + b"\xff\xef" + (len(zdata) + 2).to_bytes(2, "big") + zdata + jpeg[2:])

    # 13. Windows program disguised as a photo
    write("invoice.jpg", b"MZ\x90\x00" + b"\x00" * 60 + b"This program cannot be run in DOS mode." + bytes(200))

    # ---- Metadata ----
    # 14. Edit date set BEFORE the capture date (forged metadata)
    write("backdated.jpg", camera_jpeg(photo("portrait"), changed="2026:10:10 09:30:00"))

    # 15. Photo with GPS location (Santorini: 36 27' 42.5" N, 25 22' 31.1" E)
    write("gps.jpg", camera_jpeg(photo("santorini"), gps={
        1: "N", 2: (36.0, 27.0, 42.5), 3: "E", 4: (25.0, 22.0, 31.1)}))

    # 16. Cropped after capture, camera preview still shows the full frame
    river = photo("river")
    write("cropped.jpg", camera_jpeg(river.crop((200, 0, 840, 640)), preview=river))

    # 17. Metadata stripped (like WhatsApp / social media): a note, not proof
    photo("sneakers").save(os.path.join(folder, "stripped.jpg"), quality=95)

    return sorted(os.path.join(folder, f) for f in os.listdir(folder))


# =========================================================
# SELF-CHECK: tool must catch every planted sample
# =========================================================

def self_check(results):
    def flags(name):
        return " ".join(results[name])

    assert results["original.jpg"] == [], results["original.jpg"]
    assert "edited region" in flags("tampered.jpg") and "Photoshop" in flags("tampered.jpg")
    assert "thumbnail MISMATCH" in flags("tampered.jpg")
    assert "Modified after capture" in flags("tampered.jpg")
    assert "Copy-move" in flags("cloned.jpg") and "thumbnail" not in flags("cloned.jpg")
    assert "hidden ZIP" in flags("holiday.jpg")
    assert "LSB" in flags("stego.png")
    assert "MISMATCH" in flags("notes.txt")
    assert "end marker missing" in flags("truncated.jpg")
    assert "Unknown file signature" in flags("corrupted_header.jpg")
    assert "Corrupted image data" in flags("broken_data.jpg")
    assert "tiger@123" in flags("comment.jpg")
    assert "hidden text data after" in flags("after_iend.png")
    assert "ZIP at byte" in flags("embedded_zip.jpg")
    assert "content is EXE" in flags("invoice.jpg")
    assert "BEFORE capture" in flags("backdated.jpg")
    assert "GPS" in flags("gps.jpg")
    assert "aspect ratio differs" in flags("cropped.jpg")
    assert results["stripped.jpg"] == [], results["stripped.jpg"]
    print("\nSelf-check passed: every planted artefact was detected; original and stripped are clean.")


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image forensic analysis tool")
    parser.add_argument("files", nargs="*", help="image files to analyse")
    parser.add_argument("--demo", action="store_true", help="create and analyse sample evidence")
    parser.add_argument("--ui", action="store_true", help="open the drag-and-drop page in the browser")
    parser.add_argument("--port", type=int, default=8000, help="port for --ui (default 8000)")
    args = parser.parse_args()

    if args.ui:
        run_ui(args.port)
        sys.exit(0)

    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(here, "reports")
    os.makedirs(out_dir, exist_ok=True)

    files = make_demo(os.path.join(here, "samples")) if args.demo else args.files
    if not files:
        parser.print_help()
        sys.exit(1)

    results = {}
    for path in files:
        lines, suspicious, extras = analyse(path, out_dir)
        results[os.path.basename(path)] = (lines, suspicious, extras)
        report = os.path.join(out_dir, os.path.basename(path) + "_report.txt")
        with open(report, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("\n".join(lines))
        print(f"Report saved: {report}\n")

    print("=" * 64)
    print(" SUMMARY")
    print("=" * 64)
    for name, (_, sus, _) in results.items():
        print(f"{name:20} {'SUSPICIOUS' if sus else 'CLEAN'}")

    html_path = os.path.join(out_dir, "report.html")
    write_html(results, html_path)
    print(f"\nHTML case report: {html_path}")

    if args.demo:
        self_check({name: r[1] for name, r in results.items()})
