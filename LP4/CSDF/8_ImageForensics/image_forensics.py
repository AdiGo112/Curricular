# =========================================================
# MINI PROJECT 8
# Tool for Digital Forensics of Images
# =========================================================
#
# Checks performed on an image (evidence):
#
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
#
# A text report and an ELA image are saved for each file.
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
#
# Output goes to the "reports" folder.
#
# =========================================================

import argparse
import hashlib
import io
import os
import sys

import numpy as np
from PIL import ExifTags, Image, ImageChops

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
]

EDITING_SOFTWARE = ["photoshop", "gimp", "paint.net", "lightroom", "snapseed", "picsart", "canva"]

ELA_QUALITY = 90       # quality used to re-save the image for ELA
ELA_BLOCK = 16         # ELA is compared block by block (pixels)
ELA_THRESHOLD = 3.0    # suspicious if smoothed |z-score| > 3  (ponytail: simple z-score, tune per camera)


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
    info = {ExifTags.TAGS.get(tag, tag): value for tag, value in exif.items()}

    gps = exif.get_ifd(0x8825)   # GPS block
    if gps:
        info["GPSInfo"] = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps.items()}

    findings = []
    software = str(info.get("Software", "")).lower()
    if any(s in software for s in EDITING_SOFTWARE):
        findings.append(f"Image was processed by editing software: {info['Software']}")
    if not info:
        findings.append("No EXIF metadata (it may have been stripped)")
    if "GPSInfo" in info:
        findings.append("GPS location present in metadata")
    return info, findings


# =========================================================
# 4. HIDDEN DATA AFTER END OF IMAGE
# =========================================================

def appended_data(kind, data):
    if kind == "JPEG":
        end = data.rfind(b"\xff\xd9")
        end = -1 if end == -1 else end + 2
    elif kind == "PNG":
        end = data.rfind(b"IEND")
        end = -1 if end == -1 else end + 8      # 'IEND' + 4-byte CRC
    else:
        return 0, b""
    if end == -1 or end >= len(data):
        return 0, b""
    return len(data) - end, data[end:]


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
    blocks = diff[:h, :w].reshape(h // ELA_BLOCK, ELA_BLOCK, w // ELA_BLOCK, ELA_BLOCK).mean(axis=(1, 3))

    # A pasted region can be HIGHER or LOWER than the rest
    # (e.g. a smoother, more compressed patch), so check both.
    z = (blocks - blocks.mean()) / max(blocks.std(), 1e-6)

    # Average every block with its 8 neighbours: random noisy
    # blocks cancel out, a real pasted region stays strong.
    p = np.pad(z, 1, mode="edge")
    z = sum(p[i:i + z.shape[0], j:j + z.shape[1]] for i in range(3) for j in range(3)) / 9

    rows, cols = np.where(np.abs(z) > ELA_THRESHOLD)
    if len(rows) == 0:
        return None
    return (int(cols.min() * ELA_BLOCK), int(rows.min() * ELA_BLOCK),
            int((cols.max() + 1) * ELA_BLOCK), int((rows.max() + 1) * ELA_BLOCK), len(rows))


# =========================================================
# ANALYSE ONE FILE
# =========================================================

def analyse(path, out_dir):
    with open(path, "rb") as f:
        data = f.read()

    name = os.path.basename(path)
    lines = ["=" * 64, f" IMAGE FORENSIC REPORT: {name}", "=" * 64,
             f"File size : {len(data)} bytes"]
    suspicious = []

    for algo, value in file_hashes(data).items():
        lines.append(f"{algo:8}  : {value}")

    kind, ok, note = check_signature(path, data)
    lines.append(f"Signature : {kind} ({note})")
    if not ok:
        suspicious.append(note)

    size, blob = appended_data(kind, data)
    if size:
        msg = f"{size} bytes of hidden {describe_blob(blob)} data after end-of-image marker"
        lines.append(f"Appended  : {msg}")
        suspicious.append(msg)
    else:
        lines.append("Appended  : none")

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception as e:
        lines.append(f"Image     : cannot be opened ({e})")
        return lines, suspicious

    lines.append(f"Format    : {img.format}, {img.size[0]}x{img.size[1]}, mode {img.mode}")

    exif, exif_findings = read_exif(img)
    lines.append("\n--- EXIF metadata ---")
    lines += [f"{k}: {v}" for k, v in exif.items()] or ["(none)"]
    suspicious += [f for f in exif_findings if "No EXIF" not in f]
    lines += [f"NOTE: {f}" for f in exif_findings]

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
        region = error_level_analysis(img, ela_path)
        lines.append(f"ELA image saved: {ela_path}")
        if region:
            x1, y1, x2, y2, n = region
            msg = f"Possible edited region at ({x1},{y1})-({x2},{y2}), {n} blocks"
            lines.append(msg)
            suspicious.append(msg)
        else:
            lines.append("Uniform error level, no edited region detected")
    else:
        lines.append("Skipped (ELA applies to JPEG only)")

    lines.append("\n--- VERDICT ---")
    if suspicious:
        lines.append("SUSPICIOUS:")
        lines += [f"  - {s}" for s in suspicious]
    else:
        lines.append("No signs of tampering found")
    return lines, suspicious


# =========================================================
# DEMO: create sample evidence files
# =========================================================

def natural_image(seed, size=(480, 320)):
    rng = np.random.default_rng(seed)
    w, h = size
    y, x = np.mgrid[0:h, 0:w]
    base = np.stack([x * 255 / w, y * 255 / h, (x + y) * 127 / (w + h) + 64], axis=2)
    noise = rng.normal(0, 18, (h, w, 3))
    return Image.fromarray(np.clip(base + noise, 0, 255).astype(np.uint8))


def make_demo(folder):
    os.makedirs(folder, exist_ok=True)

    exif = Image.Exif()
    exif[0x010F] = "Canon"                 # Make
    exif[0x0110] = "Canon EOS 1500D"       # Model
    exif[0x0132] = "2026:10:15 09:30:00"   # DateTime

    # 1. Original camera photo
    natural_image(1).save(os.path.join(folder, "original.jpg"), quality=95, exif=exif)

    # 2. Tampered: object pasted from another photo, saved by Photoshop
    img = Image.open(os.path.join(folder, "original.jpg"))
    patch = natural_image(2).crop((0, 0, 120, 90))
    buf = io.BytesIO()
    patch.save(buf, "JPEG", quality=40)          # different compression history
    img.paste(Image.open(buf), (300, 180))
    exif[0x0131] = "Adobe Photoshop 25.0"         # Software
    img.save(os.path.join(folder, "tampered.jpg"), quality=95, exif=exif)

    # 3. Secret ZIP file appended after the JPEG
    with open(os.path.join(folder, "original.jpg"), "rb") as f:
        jpeg = f.read()
    zip_bytes = b"PK\x03\x04" + b"secret_plans.txt" + b"\x00" * 40
    with open(os.path.join(folder, "holiday.jpg"), "wb") as f:
        f.write(jpeg + zip_bytes)

    # 4. Message hidden with LSB steganography (PNG keeps bits exactly)
    lsb_hide(natural_image(3), "Meet at dock 7, 11pm").save(os.path.join(folder, "stego.png"))

    # 5. PNG image disguised as a text file
    natural_image(4, (64, 64)).save(os.path.join(folder, "notes.txt"), "PNG")

    return sorted(os.path.join(folder, f) for f in os.listdir(folder))


# =========================================================
# SELF-CHECK: tool must catch every planted sample
# =========================================================

def self_check(results):
    def flags(name):
        return " ".join(results[name])

    assert results["original.jpg"] == [], results["original.jpg"]
    assert "edited region" in flags("tampered.jpg") and "Photoshop" in flags("tampered.jpg")
    assert "hidden ZIP" in flags("holiday.jpg")
    assert "LSB" in flags("stego.png")
    assert "MISMATCH" in flags("notes.txt")
    print("\nSelf-check passed: every planted artefact was detected, original is clean.")


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image forensic analysis tool")
    parser.add_argument("files", nargs="*", help="image files to analyse")
    parser.add_argument("--demo", action="store_true", help="create and analyse sample evidence")
    args = parser.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(here, "reports")
    os.makedirs(out_dir, exist_ok=True)

    files = make_demo(os.path.join(here, "samples")) if args.demo else args.files
    if not files:
        parser.print_help()
        sys.exit(1)

    results = {}
    for path in files:
        lines, suspicious = analyse(path, out_dir)
        results[os.path.basename(path)] = suspicious
        report = os.path.join(out_dir, os.path.basename(path) + "_report.txt")
        with open(report, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("\n".join(lines))
        print(f"Report saved: {report}\n")

    print("=" * 64)
    print(" SUMMARY")
    print("=" * 64)
    for name, sus in results.items():
        print(f"{name:20} {'SUSPICIOUS' if sus else 'CLEAN'}")

    if args.demo:
        self_check(results)
