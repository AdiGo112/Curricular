# Assignment 4: Recovering Permanently Deleted Files and Deleted Partitions

## Aim

Write a computer forensic application program for recovering permanently deleted files and deleted partitions.

## Theory and Fundamentals

### What "delete" really does
Deleting a file does **not** erase its data. The operating system only marks the file's directory entry as free and releases its clusters. The bytes stay on the disk until new data overwrites them. Therefore deleted files are often recoverable. Truly destroying data needs **secure wiping** (overwriting) or, for SSDs, encryption plus TRIM.

### Disk basics
- **Sector:** smallest disk unit, 512 bytes here. **LBA** (Logical Block Address) = sector number.
- **Cluster:** group of sectors used by FAT (here 8 sectors = 4 KB).
- **Disk image:** a bit-for-bit copy (`dd`, FTK Imager). Forensic work is done on the image, never on the original, and the image is hashed.
- **Write blocker:** hardware/software that lets the investigator read a disk without any chance of writing to it.

### MBR and the partition table
The **Master Boot Record** is sector 0 of the disk.

| Offset | Size | Content |
| --- | --- | --- |
| 0 | 446 | Boot code |
| 446 | 4 x 16 | **Partition table**: 4 entries |
| 510 | 2 | Signature `55 AA` |

Each 16-byte entry holds the type byte (e.g. `0x0C` FAT32 LBA, `0x07` NTFS/exFAT, `0x83` Linux), the start LBA (offset 8) and the number of sectors (offset 12), both little-endian 32-bit. (GPT is the modern replacement for MBR.)

**Deleting a partition** only clears its 16-byte entry. The partition's own **boot sector** (first sector of the partition) still sits on disk, so the partition can be found again by searching for boot-sector signatures.

### FAT32 structure
Order on a FAT32 partition: *boot sector (BPB) -> reserved sectors -> two FATs -> data area*. The **FAT** is a table that chains clusters of a file. The root directory is stored in the data area, in clusters, as **32-byte directory entries**:

| Offset | Size | Field |
| --- | --- | --- |
| 0 | 8 | Name (first byte `0xE5` = **deleted**, `0x00` = end of directory) |
| 8 | 3 | Extension |
| 11 | 1 | Attributes (`0x0F` long-name entry, `0x08` volume label) |
| 20 / 26 | 2 + 2 | First cluster (high / low part) |
| 28 | 4 | File size |

Deleting a file changes the first byte of the name to `0xE5` and frees its FAT chain. The size and first cluster remain, so a file stored in **contiguous** clusters can be rebuilt: read `size` bytes from the first cluster. The first letter of the name is lost, hence recovered names start with `_`.

### File carving
**Carving** recovers files without any file-system information, by scanning raw data for **magic numbers** (file signatures): a header at the start and often a footer at the end. It works after formatting or when directory entries are overwritten, but it loses the filename and fails for fragmented files.

| Type | Header | Footer |
| --- | --- | --- |
| JPEG | `FF D8 FF` | `FF D9` |
| PNG | `89 50 4E 47 0D 0A 1A 0A` | `IEND` + 4-byte CRC |
| PDF | `%PDF-` | `%%EOF` |
| ZIP / DOCX / XLSX | `PK 03 04` | `PK 05 06` + 18 more bytes |

### Integrity of recovered evidence
Each recovered file and the image are hashed (MD5, SHA-256) so that the evidence can be proved unchanged and matched with the original.

## How the Code Works

File: `4_DataRecovery/recover.py` (standard library + Pillow, the latter only to build demo JPEG/PNG files). The whole image is read into memory and **never modified**; repaired output goes to a *copy*.

### A) Partition recovery
- `read_mbr(img)` checks `55 AA` and reads the 4 entries; this is the "current" table.
- `scan_boot_sectors(img)` walks every sector (LBA 1 onwards) and recognises:
  - **FAT32:** `"FAT32   "` at offset 82, `55 AA` at 510 and bytes-per-sector = 512.
  - **NTFS:** `"NTFS    "` at offset 3 (total sectors = field + 1).
  - A candidate is accepted only if its **"hidden sectors" field equals its own LBA**. This rules out the backup boot sector that FAT32 keeps inside the partition.
```python
if hidden == lba:      # "hidden sectors" = partition start: rules out backup copies
    found.append({"type": 0x0C, "start": lba, "sectors": total, ...})
```
- `write_mbr_entries()` builds a new MBR with the found partitions, and `recover()` writes `recovered_disk.img` (new MBR + the rest of the original image).

### B) FAT32 undelete: `fat32_undelete(img, part)`
Reads the boot sector (sectors per cluster, reserved sectors, number and size of FATs, root cluster), computes where the data area starts, reads the root directory and loops over 32-byte entries:
```python
if e[0] == 0x00: break                       # end of directory
if attr == 0x0F or attr & 0x08: continue     # long-name entry or volume label
...
if e[0] == 0xE5:
    off, _ = cluster(first)
    data = img[off:off + size]               # assume contiguous
```
Live files are listed; deleted ones are copied out as `_HOTO.JPG` etc. Only the root directory and contiguous files are handled.

### C) Carving: `carve(img)`
For every sector start, check each signature in `SIGNATURES`; if the header matches, search for the footer within `MAX_FILE` (20 MB), add the extra bytes (PNG CRC, ZIP end record + comment length, PDF trailing newline) and cut the file out. Files are saved as `carved_NN_at_<offset>.<ext>`.

### Demo disk: `build_demo_disk()`
Builds a 5 MB image: a 3 MB FAT32 partition at LBA 2048 and a 1 MB NTFS partition at LBA 8192; five files (`PHOTO.JPG`, `CHART.PNG`, `REPORT.PDF`, `LEDGER.ZIP`, `NOTES.TXT`) get `0xE5` entries; `README.TXT` stays; a **second copy of the photo** is written with no directory entry (only carving can find it); finally the MBR partition entries are **zeroed** to simulate deleted partitions. The self-check asserts every file matches the original byte for byte.

## How to Run and Expected Output

```bash
python LP4/CSDF/4_DataRecovery/recover.py --demo        # build sample disk and recover
python LP4/CSDF/4_DataRecovery/recover.py usb.img       # your own image
```
Make an image first (never work on the original): Linux `sudo dd if=/dev/sdb of=usb.img bs=4M status=progress`; Windows: FTK Imager -> Create Disk Image -> Raw (dd).

Real output (trimmed):

```
--- A) Partition table (MBR) ---
  (empty: partitions deleted)
Partitions found by scanning boot sectors:
  FAT32 (LBA)  start LBA   2048  size 3.0 MB  label 'EVIDENCE'
  NTFS/exFAT   start LBA   8192  size 1.0 MB  label 'NTFS'
2 deleted partition(s) restored in COPY: ...\recovered\recovered_disk.img
--- B) FAT32 undelete (partition at LBA 2048) ---
Existing files: README.TXT
  RECOVERED _HOTO.JPG          2878 bytes  cluster    3  SHA-256 70439bb27571c86e...
  RECOVERED _OTES.TXT           520 bytes  cluster    7  ...
--- C) File carving (signature search over all sectors) ---
  JPEG image         offset   1077248      2878 bytes  -> carved_01_at_1077248.jpg
  JPEG image         offset   1110016      2878 bytes  -> carved_05_at_1110016.jpg
Total recovered: 10 files
Self-check passed: both partitions restored; every deleted file recovered byte-for-byte ...
```

Outputs are in `4_DataRecovery/recovered/` (`undeleted/`, `carved/`, `recovered_disk.img`, `recovery_report.txt`). Notice: `NOTES.TXT` has no signature, so only undelete recovers it; the orphan JPEG at offset 1110016 is found only by carving.

## Related Concepts and Real-World Tools

- **Autopsy / The Sleuth Kit:** open-source forensic suite (`fls`, `icat`, `tsk_recover`) with timeline and keyword search.
- **FTK / FTK Imager, EnCase, X-Ways:** commercial suites; FTK Imager makes raw images and hashes them.
- **PhotoRec / TestDisk:** PhotoRec carves by signature; TestDisk rebuilds deleted partitions and boot sectors (the same idea as part A).
- **Foremost, Scalpel, Recuva.**
- **NTFS:** uses the **MFT** (Master File Table); deleted files keep an MFT record, `$UsnJrnl` and `$LogFile` give extra evidence.
- **Anti-forensics:** secure erase (`shred`, DBAN), SSD **TRIM** and encryption make recovery fail.
- **Slack space and unallocated space** are where leftover data is found.
- **Legal:** IT Act 2000 Section 65 (tampering with computer source documents), 66; Section 79A (Examiner of Electronic Evidence); electronic records are admitted under Section 65B of the Indian Evidence Act (now Section 63 of the Bharatiya Sakshya Adhiniyam, 2023), which is why hashes matter.

## Viva Questions

1. **What happens when a file is deleted on FAT32?** The first byte of its directory entry becomes `0xE5` and its clusters are marked free; the data stays until overwritten.
2. **Why do recovered file names begin with an underscore?** The first character of the name was overwritten by `0xE5` and cannot be known, so the program writes `_` in its place.
3. **What does the MBR contain and where is the partition table?** Sector 0: boot code (446 bytes), 4 partition entries of 16 bytes at offset 446, and the signature `55 AA` at offset 510.
4. **How can a deleted partition be recovered?** Deleting only clears the MBR entry; the partition's boot sector remains. The program scans all sectors for FAT32/NTFS boot-sector signatures and rebuilds the entries.
5. **Why compare the "hidden sectors" field with the sector number?** It records the partition's start LBA. If it equals the sector where we found the signature, it is the real boot sector and not the backup copy.
6. **What is file carving and when is it used?** Recovering files by searching for header/footer magic numbers in raw data. Used when directory information is gone (formatted or overwritten), at the cost of losing filenames.
7. **What are the limits of the undelete and carving methods?** Undelete assumes contiguous clusters; carving fails for fragmented files; overwritten clusters are lost; SSD TRIM and wiping destroy data.
8. **Why work on an image and why hash it?** The original must stay unchanged; the hash proves the image and recovered files are exact, supporting admissibility and chain of custody.
9. **What is a magic number?** The first bytes that identify a file type, e.g. `FF D8 FF` for JPEG, `%PDF-` for PDF, `PK 03 04` for ZIP/DOCX.
10. **Which tools do professionals use for the same job?** Autopsy/Sleuth Kit, FTK, EnCase, PhotoRec and TestDisk.
