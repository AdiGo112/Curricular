# =========================================================
# ASSIGNMENT 4
# Recover Permanently Deleted Files and Deleted Partitions
# =========================================================
#
# Works on a RAW DISK IMAGE (the evidence is never modified).
#
# A) PARTITION RECOVERY
#    Deleting a partition only clears its 16-byte entry in the
#    MBR. The partition's boot sector is still on the disk, so
#    we scan every sector for boot-sector signatures:
#        FAT32 : "FAT32   " at offset 82 and 0x55AA at 510
#        NTFS  : "NTFS    " at offset 3  and 0x55AA at 510
#    and rebuild the partition table in a COPY of the image.
#
# B) FILE UNDELETE (FAT32)
#    Deleting a file only changes the first byte of its 32-byte
#    directory entry to 0xE5; name, size and first cluster stay.
#    We read the directory, find 0xE5 entries and copy the
#    clusters back (assuming the file was stored contiguously).
#
# C) FILE CARVING (any file system, even after formatting)
#    Search raw sectors for file signatures (header ... footer):
#        JPEG FF D8 FF ... FF D9      PNG 89 50 4E 47 ... IEND
#        PDF  %PDF- ... %%EOF         ZIP/DOCX PK 03 04 ... PK 05 06
#
# Every recovered file gets an MD5 + SHA-256 hash in the report.
#
# =========================================================
# HOW TO RUN
# =========================================================
#
#   python recover.py --demo        build a sample disk with deleted
#                                   files + deleted partitions, recover them
#   python recover.py usb.img       recover from your own image
#
# Make an image of a USB drive first (never work on the original):
#   Linux  : sudo dd if=/dev/sdb of=usb.img bs=4M status=progress
#   Windows: FTK Imager > Create Disk Image > Raw (dd)
#
# =========================================================

import argparse
import hashlib
import io
import os
import shutil
import struct
import sys
import zipfile

SECTOR = 512
PART_TYPES = {0x0C: "FAT32 (LBA)", 0x0B: "FAT32", 0x07: "NTFS/exFAT", 0x83: "Linux", 0x00: "empty"}

SIGNATURES = [
    # (name, extension, header, footer, extra bytes after footer)
    ("JPEG image", "jpg", b"\xff\xd8\xff", b"\xff\xd9", 0),
    ("PNG image", "png", b"\x89PNG\r\n\x1a\n", b"IEND", 4),
    ("PDF document", "pdf", b"%PDF-", b"%%EOF", 0),
    ("ZIP / DOCX / XLSX", "zip", b"PK\x03\x04", b"PK\x05\x06", 18),
]
MAX_FILE = 20 * 1024 * 1024


def hashes(data):
    return hashlib.md5(data).hexdigest(), hashlib.sha256(data).hexdigest()


# =========================================================
# A) PARTITIONS
# =========================================================

def read_mbr(img):
    if img[510:512] != b"\x55\xaa":
        return []
    parts = []
    for i in range(4):
        e = img[446 + 16 * i: 462 + 16 * i]
        ptype, start, count = e[4], *struct.unpack("<II", e[8:16])
        if ptype and count:
            parts.append({"type": ptype, "start": start, "sectors": count})
    return parts


def scan_boot_sectors(img):
    """Find partitions by their boot sectors, even if the MBR entry is gone."""
    found = []
    for lba in range(1, len(img) // SECTOR):
        s = img[lba * SECTOR:(lba + 1) * SECTOR]
        if s[510:512] != b"\x55\xaa":
            continue
        if s[82:90] == b"FAT32   " and struct.unpack("<H", s[11:13])[0] == SECTOR:
            total = struct.unpack("<I", s[32:36])[0]
            hidden = struct.unpack("<I", s[28:32])[0]
            if hidden == lba:                     # "hidden sectors" = partition start: rules out backup copies
                found.append({"type": 0x0C, "start": lba, "sectors": total, "label": s[71:82].decode(errors="replace").strip()})
        elif s[3:11] == b"NTFS    ":
            total = struct.unpack("<Q", s[40:48])[0] + 1   # NTFS stores (size - 1)
            hidden = struct.unpack("<I", s[28:32])[0]
            if hidden == lba:
                found.append({"type": 0x07, "start": lba, "sectors": total, "label": "NTFS"})
    return found


def write_mbr_entries(img, parts):
    mbr = bytearray(img[:SECTOR])
    mbr[446:510] = bytes(64)
    for i, p in enumerate(parts[:4]):
        mbr[446 + 16 * i: 462 + 16 * i] = (b"\x00\xfe\xff\xff" + bytes([p["type"]]) + b"\xfe\xff\xff"
                                           + struct.pack("<II", p["start"], p["sectors"]))
    mbr[510:512] = b"\x55\xaa"
    return bytes(mbr)


# =========================================================
# B) FAT32 UNDELETE
# =========================================================

def fat32_undelete(img, part):
    base = part["start"] * SECTOR
    bs = img[base:base + SECTOR]
    sec_per_clus = bs[13]
    reserved = struct.unpack("<H", bs[14:16])[0]
    nfats = bs[16]
    fat_size = struct.unpack("<I", bs[36:40])[0]
    root_cluster = struct.unpack("<I", bs[44:48])[0]
    data_start = base + (reserved + nfats * fat_size) * SECTOR
    cluster_bytes = sec_per_clus * SECTOR

    def cluster(n):
        off = data_start + (n - 2) * cluster_bytes
        return off, img[off:off + cluster_bytes]

    _, root = cluster(root_cluster)
    live, deleted = [], []
    for i in range(0, len(root), 32):
        e = root[i:i + 32]
        if e[0] == 0x00:
            break                                 # end of directory
        attr = e[11]
        if attr == 0x0F or attr & 0x08:           # long-name entry or volume label
            continue
        name = e[0:8].decode("latin-1").rstrip()
        ext = e[8:11].decode("latin-1").rstrip()
        first = (struct.unpack("<H", e[20:22])[0] << 16) | struct.unpack("<H", e[26:28])[0]
        size = struct.unpack("<I", e[28:32])[0]
        if e[0] == 0xE5:
            off, _ = cluster(first)
            data = img[off:off + size]
            deleted.append(("_" + name[1:] + ("." + ext if ext else ""), size, first, data))
        else:
            live.append(name + ("." + ext if ext else ""))
    return live, deleted


# =========================================================
# C) CARVING
# =========================================================

def carve(img):
    results = []
    for lba in range(len(img) // SECTOR):
        off = lba * SECTOR
        for name, ext, header, footer, extra in SIGNATURES:
            if img.startswith(header, off):
                end = img.find(footer, off + len(header), off + MAX_FILE)
                if end == -1:
                    continue
                end += len(footer) + extra
                if ext == "zip":                      # add the archive comment length
                    end += struct.unpack("<H", img[end - 2:end])[0]
                if ext == "pdf":                      # PDFs normally end with a line break after %%EOF
                    end += 2 if img[end:end + 2] == b"\r\n" else 1 if img[end:end + 1] in (b"\n", b"\r") else 0
                results.append((name, ext, off, img[off:end]))
    return results


# =========================================================
# MAIN ANALYSIS
# =========================================================

def recover(image_path, out_dir):
    with open(image_path, "rb") as f:
        img = f.read()
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(os.path.join(out_dir, "undeleted"))
    os.makedirs(os.path.join(out_dir, "carved"))

    md5, sha = hashes(img)
    report = ["=" * 70, f" DATA RECOVERY REPORT: {os.path.basename(image_path)}", "=" * 70,
              f"Image size: {len(img):,} bytes ({len(img) // SECTOR} sectors)",
              f"Image MD5 : {md5}", f"Image SHA-256: {sha}"]

    # ---- A ----
    report.append("\n--- A) Partition table (MBR) ---")
    current = read_mbr(img)
    report += [f"  {PART_TYPES.get(p['type'], hex(p['type']))} start {p['start']}" for p in current] or ["  (empty: partitions deleted)"]
    found = scan_boot_sectors(img)
    report.append("Partitions found by scanning boot sectors:")
    for p in found:
        report.append(f"  {PART_TYPES[p['type']]:12} start LBA {p['start']:6}  size {p['sectors'] * SECTOR / 1048576:.1f} MB  label '{p['label']}'")
    lost = [p for p in found if p["start"] not in {c["start"] for c in current}]
    if lost:
        fixed = os.path.join(out_dir, "recovered_disk.img")
        with open(fixed, "wb") as f:
            f.write(write_mbr_entries(img, found) + img[SECTOR:])
        report.append(f"{len(lost)} deleted partition(s) restored in COPY: {fixed}")

    # ---- B ----
    recovered = {}
    for p in found:
        if p["type"] != 0x0C:
            continue
        live, deleted = fat32_undelete(img, p)
        report.append(f"\n--- B) FAT32 undelete (partition at LBA {p['start']}) ---")
        report.append(f"Existing files: {', '.join(live) or 'none'}")
        for name, size, first, data in deleted:
            path = os.path.join(out_dir, "undeleted", name)
            with open(path, "wb") as f:
                f.write(data)
            recovered[name] = data
            report.append(f"  RECOVERED {name:14} {size:8} bytes  cluster {first:4}  SHA-256 {hashes(data)[1][:16]}...")

    # ---- C ----
    report.append("\n--- C) File carving (signature search over all sectors) ---")
    carved = carve(img)
    for i, (name, ext, off, data) in enumerate(carved, 1):
        fname = f"carved_{i:02d}_at_{off}.{ext}"
        with open(os.path.join(out_dir, "carved", fname), "wb") as f:
            f.write(data)
        recovered[fname] = data
        report.append(f"  {name:18} offset {off:9}  {len(data):8} bytes  -> {fname}")

    report.append(f"\nTotal recovered: {len(recovered)} files in {out_dir}")
    text = "\n".join(report)
    with open(os.path.join(out_dir, "recovery_report.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    return text, found, recovered


# =========================================================
# DEMO DISK
# =========================================================

def sample_files():
    from PIL import Image, ImageDraw
    files = {}
    img = Image.new("RGB", (320, 200), (30, 90, 160))
    ImageDraw.Draw(img).text((20, 90), "CONFIDENTIAL PHOTO", fill="white")
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    files["PHOTO.JPG"] = buf.getvalue()

    img = Image.new("RGB", (200, 120), "white")
    d = ImageDraw.Draw(img)
    for i, h in enumerate((40, 80, 60, 100)):
        d.rectangle([20 + i * 45, 110 - h, 50 + i * 45, 110], fill=(200, 60, 40))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    files["CHART.PNG"] = buf.getvalue()

    files["REPORT.PDF"] = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
                           b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
                           b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 100]>>endobj\n"
                           b"trailer<</Root 1 0 R>>\n%%EOF\n")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("accounts.txt", "Account 4521: Rs 4,50,000 transferred on 20-10-2026\n" * 20)
    files["LEDGER.ZIP"] = buf.getvalue()

    files["NOTES.TXT"] = b"Meeting with buyer on Friday 7 pm near the station.\n" * 10   # no signature: undelete only
    files["README.TXT"] = b"This USB drive belongs to the accounts department.\n"          # not deleted
    return files


def build_demo_disk(path):
    files = sample_files()
    p1_start, p1_size = 2048, 6144                 # FAT32 partition: 3 MB
    p2_start, p2_size = 8192, 2048                 # NTFS partition: 1 MB
    disk = bytearray((p2_start + p2_size) * SECTOR)

    # ---- FAT32 boot sector (minimal but valid layout) ----
    spc, reserved, nfats, fat_size, root = 8, 32, 2, 8, 2
    bs = bytearray(SECTOR)
    bs[0:3] = b"\xeb\x58\x90"
    bs[3:11] = b"MSDOS5.0"
    struct.pack_into("<HBHBHHBHHHII", bs, 11, SECTOR, spc, reserved, nfats, 0, 0, 0xF8, 0, 63, 255, p1_start, p1_size)
    struct.pack_into("<IHHIHH", bs, 36, fat_size, 0, 0, root, 1, 6)
    bs[66] = 0x29
    struct.pack_into("<I", bs, 67, 0x1A2B3C4D)
    bs[71:82] = b"EVIDENCE   "
    bs[82:90] = b"FAT32   "
    bs[510:512] = b"\x55\xaa"
    base = p1_start * SECTOR
    disk[base:base + SECTOR] = bs

    data_start = base + (reserved + nfats * fat_size) * SECTOR
    cbytes = spc * SECTOR

    # ---- files in clusters + directory entries ----
    entries = bytearray()
    label = b"EVIDENCE   " + bytes([0x08]) + bytes(20)
    entries += label
    next_cluster = 3
    deleted_names = {"PHOTO.JPG", "CHART.PNG", "REPORT.PDF", "LEDGER.ZIP", "NOTES.TXT"}
    for name, data in files.items():
        stem, ext = name.split(".")
        off = data_start + (next_cluster - 2) * cbytes
        disk[off:off + len(data)] = data
        e = bytearray(stem.ljust(8).encode() + ext.ljust(3).encode() + bytes(21))
        e[11] = 0x20                                          # archive attribute
        struct.pack_into("<H", e, 20, next_cluster >> 16)
        struct.pack_into("<H", e, 26, next_cluster & 0xFFFF)
        struct.pack_into("<I", e, 28, len(data))
        if name in deleted_names:
            e[0] = 0xE5                                       # <- this is all "delete" does
        entries += e
        next_cluster += -(-len(data) // cbytes)

    # A second photo whose directory entry was overwritten: only carving can find it
    off = data_start + next_cluster * cbytes
    disk[off:off + len(files["PHOTO.JPG"])] = files["PHOTO.JPG"]

    root_off = data_start + (root - 2) * cbytes
    disk[root_off:root_off + len(entries)] = entries

    # ---- NTFS boot sector ----
    ntfs = bytearray(SECTOR)
    ntfs[0:3] = b"\xeb\x52\x90"
    ntfs[3:11] = b"NTFS    "
    struct.pack_into("<HB", ntfs, 11, SECTOR, 8)
    struct.pack_into("<I", ntfs, 28, p2_start)
    struct.pack_into("<Q", ntfs, 40, p2_size - 1)
    ntfs[510:512] = b"\x55\xaa"
    disk[p2_start * SECTOR:(p2_start + 1) * SECTOR] = ntfs

    # ---- MBR with both partitions DELETED (entries zeroed) ----
    disk[0:SECTOR] = write_mbr_entries(bytes(disk), [])
    with open(path, "wb") as f:
        f.write(disk)
    return files, deleted_names


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deleted file and partition recovery")
    parser.add_argument("image", nargs="?", help="raw disk image (.img / .dd)")
    parser.add_argument("--demo", action="store_true", help="build and recover a sample disk")
    args = parser.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "recovered")

    if args.demo:
        image = os.path.join(here, "evidence_usb.img")
        originals, deleted_names = build_demo_disk(image)
        print(f"Demo disk created: {image}  (2 partitions deleted, 5 files deleted)\n")
    elif args.image:
        image = args.image
    else:
        parser.print_help()
        sys.exit(1)

    text, found, recovered = recover(image, out)
    print(text)

    if args.demo:
        assert [p["type"] for p in found] == [0x0C, 0x07], found
        assert read_mbr(open(os.path.join(out, "recovered_disk.img"), "rb").read()) != []
        for name in deleted_names:
            got = recovered["_" + name[1:]]
            assert got == originals[name], f"{name} not recovered exactly"
        carved = [d for n, d in recovered.items() if n.startswith("carved")]
        for name in ("PHOTO.JPG", "CHART.PNG", "REPORT.PDF", "LEDGER.ZIP"):
            assert originals[name] in carved, f"{name} not carved"
        assert sum(d == originals["PHOTO.JPG"] for d in carved) == 2, "orphan photo not carved"
        assert zipfile.ZipFile(io.BytesIO(recovered["_EDGER.ZIP"])).read("accounts.txt").startswith(b"Account")
        print("\nSelf-check passed: both partitions restored; every deleted file recovered byte-for-byte "
              "(hashes match); orphan photo found only by carving.")
