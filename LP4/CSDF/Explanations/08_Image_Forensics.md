# Assignment 8 (Mini Project): Digital Forensics of Images

## Aim

Design and develop a tool for digital forensics of images.

## Theory and Fundamentals

### Why image forensics?
Images are used as evidence (accident photos, ID proofs, harassment cases) and are easy to edit, disguise or use to hide secrets. Image forensics answers: *Is it authentic? Who made it? Was it edited? Is something hidden in it?*

### Hashing and integrity
A **cryptographic hash** (MD5, SHA-1, SHA-256) is a fixed-length fingerprint of a file. Changing even one bit changes the hash completely. A hash taken at seizure time and checked later proves the file is unchanged. MD5 and SHA-1 have known collision weaknesses, so SHA-256 is preferred; forensic tools record several.

### File signatures (magic numbers)
The first bytes of a file identify its true type regardless of the extension. A file named `notes.txt` that starts with `89 50 4E 47` is really a PNG: it was **renamed / disguised**.

| Format | Starts with |
| --- | --- |
| JPEG | `FF D8 FF` (ends with `FF D9`) |
| PNG | `89 50 4E 47 0D 0A 1A 0A` (ends with `IEND` + CRC) |
| GIF | `GIF87a` / `GIF89a` |
| BMP | `BM` |
| ZIP | `PK 03 04` |
| PDF | `%PDF` |

### EXIF metadata
**EXIF** (Exchangeable Image File Format) data is stored inside JPEGs by cameras and software: make, model, date/time, exposure, **GPS location**, and the **Software** tag. Useful for linking a photo to a device, time and place, and for spotting editing programs (Photoshop, GIMP). Absence of EXIF can mean it was stripped (social media does this). Metadata is easy to edit, so it is a clue, not proof.

### Data hidden after the image (appended data)
Image viewers stop reading at the end marker (JPEG `FF D9`, PNG `IEND`). Anything appended after it, such as a ZIP, is ignored by viewers but remains in the file.

### Steganography and LSB
**Steganography** hides the *existence* of a message (cryptography hides its *meaning*). In **LSB (Least Significant Bit)** steganography, each message bit replaces the lowest bit of a pixel value. Changing the lowest bit alters the colour by at most 1/255, which the eye cannot notice. It needs a **lossless** format (PNG, BMP); JPEG compression would destroy the bits. Detection: extract the LSBs and see if they form readable text (**steganalysis**).

### JPEG compression and Error Level Analysis (ELA)
JPEG is **lossy**: each save re-quantises the image. An untouched photo has a fairly uniform "compression history". If a region from another image (different compression level) is pasted in, it reacts differently when the whole image is re-saved at a known quality. **ELA** re-saves the JPEG at e.g. quality 90, subtracts it from the original, and displays the difference. Regions with a clearly different error level are suspicious. ELA is a *hint*: false positives occur on sharp edges, text and heavily processed images.

### EXIF thumbnail mismatch
Cameras store a small preview JPEG (about 160x120) inside the EXIF block (in IFD1). Many editors change the main image but leave the old preview untouched. If the preview no longer looks like the image, the image was changed after it was taken. If the preview's aspect ratio differs, the image was probably cropped.

### Timestamp consistency
EXIF has `DateTimeOriginal` (when the photo was taken) and `DateTime` (when it was last changed, usually set by editing software). The file system has its own modified time. Red flags: changed long after capture (edited), changed *before* capture (impossible, so forged), a date in the future, or an EXIF date later than the file's own modified time.

### Copy-move (clone) forgery
Part of an image is copied to another place in the *same* image, to hide an object or duplicate one. ELA often misses it because the copy has the same compression history. Detection: split the image into overlapping blocks, describe each block with a few numbers, sort them so identical blocks sit next to each other, and look for many block pairs that are all moved by the **same offset** (shift vector). Random look-alike blocks have random offsets; a real clone gives one offset again and again.

### Corrupted files
A file can be damaged by an interrupted download (cut short: no end marker), a wiped header (the file signature is gone, so nothing recognises the file), or bad sectors / bit rot (random bytes in the middle). Inside JPEG compressed data a `0xFF` byte may only be followed by `00` (stuffing), `D0`-`D7` (restart markers), `D9` (end) or, in progressive JPEGs, a few table/scan markers. Random damage produces other values almost at once, so counting invalid markers detects it even when the header is fine.

### Data hidden inside the file
Besides appending data after the end marker, data can be hidden **inside** the file: a ZIP placed in an unused application segment (APP15) of the JPEG header, or text in a JPEG **comment** (COM, `FF FE`) or PNG **text chunk** (`tEXt`). Viewers ignore all of these. Searching the whole file for known signatures (`PK 03 04`, `%PDF-`, `Rar!`, `MZ`...) is called **file carving**.

### Other image forensic ideas (not coded)
PRNU camera noise fingerprint (identify the camera), lighting/shadow inconsistencies, double JPEG compression analysis, reverse image search.

## How the Code Works

File: `8_ImageForensics/image_forensics.py` (Pillow + NumPy). `analyse(path, out_dir)` runs the checks below and collects anything unusual in a `suspicious` list; the file is `CLEAN` if the list is empty.

| # | Function | What it does |
| --- | --- | --- |
| 0 | `os.stat` in `analyse` | Report generation time, file size, last modified and last accessed timestamps |
| 1 | `file_hashes` | MD5, SHA-1, SHA-256 of the file bytes |
| 2 | `check_signature` | Compares leading bytes with the `SIGNATURES` table and the extension; reports `MISMATCH` |
| 3 | `read_exif` | Reads EXIF and the GPS block; decodes GPS degrees/minutes/seconds to decimal latitude, longitude (`gps_decimal`); flags `Software` containing photoshop/gimp/paint.net/lightroom/snapseed/picsart/canva, GPS present, or EXIF missing |
| 4 | `appended_data` | JPEG: bytes after the last `FF D9`; PNG: after `IEND` + 4 CRC bytes; reports size and type of the hidden blob; reports "end marker not found (file may be corrupted/truncated)" if the marker is missing |
| 5 | `lsb_extract` | Reads the lowest bit of the first 4000 red-channel values, packs them into bytes, stops at a 0 byte; reports only if the result is at least 4 printable ASCII characters |
| 6 | `error_level_analysis` | ELA (JPEG only), see below |
| 7 | `check_thumbnail` | Finds the preview JPEG in the EXIF (APP1) segment (`exif_thumbnail`), shrinks both preview and image to a 32-pixel-wide grid and flags a cell difference above 25, or an aspect-ratio difference (cropping) |
| 8 | `check_timestamps` | Compares `DateTimeOriginal`, `DateTime` and the file modified time (see rules above) |
| 9 | `copy_move` | Block-matching clone detection, see below |
| 10 | `corrupt_scan_markers` | Counts invalid `FF xx` markers in JPEG compressed data (damage); `jpeg_segments` walks the header to find where the image data starts |
| 11 | `embedded_files` | Searches the whole file (except offset 0 and the appended part) for ZIP, PDF, RAR, 7-Zip, PNG and EXE signatures |
| 12 | `text_comments` | JPEG comment segments and PNG text chunks; any text is flagged for review |
| - | missing end marker / cannot decode | Both are now reported as suspicious; an EXE signature (`MZ`) was added to the signature table |
| - | `write_html` | One HTML case report for all files |

`read_exif` also reads the Exif sub-block (tag `0x8769`), which is where real cameras keep `DateTimeOriginal`, exposure and ISO.

Note: "No EXIF" is shown in the report but is **not** counted as suspicious (`suspicious += [f for f in exif_findings if "No EXIF" not in f]`).

### LSB hide and extract
```python
bits = np.unpackbits(np.frombuffer(message.encode() + b"\x00", dtype=np.uint8))
red[: len(bits)] = (red[: len(bits)] & 0xFE) | bits      # clear lowest bit, write message bit
```
The message ends with a zero byte so extraction knows where to stop. `lsb_hide` is used by the demo to create `stego.png`.

### ELA with block statistics
```python
rgb.save(buf, "JPEG", quality=ELA_QUALITY)                       # re-save at 90
diff = np.asarray(ImageChops.difference(rgb, resaved), dtype=np.float32).mean(axis=2)
```
1. The brightened difference image is saved as `<name>_ELA.png`.
2. The difference is averaged in 16x16 pixel blocks (`ELA_BLOCK`).
3. **Texture correction:** detailed areas (leaves, tiles, text) always have a high error level and smooth areas (sky) a low one, which is the main source of ELA false alarms. Each block's error is divided by (block texture + 5), where texture is the standard deviation of the block's brightness (`ELA_TEXTURE`). What remains is mostly the compression history.
4. Each block gets a **z-score** (distance from the mean in standard deviations). Blocks can be abnormally high *or* low, so the absolute value is used.
5. Each block is averaged with its 8 neighbours so isolated noisy blocks cancel while a real pasted region stays strong.
6. If at least 4 blocks (`ELA_MIN_BLOCKS`) have `|z| > 3.0` (`ELA_THRESHOLD`), they are reported as a bounding box.
7. ELA statistics are printed: max error difference, average block error, suspicious blocks (count and %), and a **tampering suspicion** level: LOW (no suspicious blocks), MEDIUM (up to 5%, localised paste/clone), HIGH (over 5%).

### Copy-move detection: `copy_move()`
1. Grey-scale the image; photos larger than 1024 px are shrunk first so it stays fast (about 0.7 s for a 960x640 photo).
2. A 16x16 block starts at **every pixel**, so a region moved by any number of pixels has an exact twin. Each block is described by its 4x4 grid of average brightness (16 numbers), computed fast with a summed-area table.
3. Skip flat blocks (standard deviation below 8): sky and walls match by accident.
4. Sort the blocks along the direction they differ most (first principal component) so similar blocks sit next to each other, then compare each block with its 8 nearest neighbours in that order. Two blocks "match" if no number differs by 2 or more grey levels (JPEG noise), and they are at least 24 px apart.
5. If one offset (dx, dy) appears for 200 or more matching pairs, report both regions. The tool cannot tell which is the original and which is the copy, so it says the two regions are identical.

### How the thresholds were chosen (accuracy on real photos)
The first version was tuned on synthetic images. On 24 real photos it raised false alarms on 9 (ELA) and 4 (copy-move), and found only 5 of 24 clones, because blocks were sampled every 4 pixels and a real clone rarely lands on that grid. Both detectors were rewritten and re-tuned on the same 24 photos, each also copied with a 160x120 patch pasted in and with a 128x96 region cloned elsewhere:

| Detector | False alarms (24 clean photos) | Detected |
| --- | --- | --- |
| ELA before (plain z-score) | 9 | 13/24 pastes |
| ELA now (texture correction, min 4 blocks) | **0** | **18/24** pastes |
| Copy-move before (every 4 px, exact match) | 4 | 5/24 clones |
| Copy-move now (every pixel, tolerance) | **0** | **19/24** clones |

The 5 missed clones were all copies of near-flat areas (sky, blur), which no one can see either. ELA is weaker on **large** pastes: a patch covering about 16% of the photo shifts the photo-wide mean, and only about half of a set of bicycle pastes on different photos were found. This is a real ELA limitation and a good viva point. 24 photos is a small test set; if your own photos give false alarms, re-tune `ELA_*` and `CLONE_*` at the top of the file.

### HTML case report: `write_html()`
`reports/report.html` is one self-contained page: a summary table (file, CLEAN/SUSPICIOUS, number of findings), then for each file the evidence image with cloned regions boxed in red, the ELA image with the suspected edit boxed in yellow, the findings list, and the full text report in a collapsible section. Images are embedded as base64, so the single file can be shared or submitted.

### Drag-and-drop UI: `--ui`
`run_ui()` starts Python's built-in web server (`http.server`) on `127.0.0.1:8000` and opens the page in the browser. The page (`UPLOAD_PAGE`) has a drop zone (also click-to-choose). On **Analyse**, the browser reads each file, sends it to `/analyse`, and `UIHandler.do_POST`:
1. writes the exact bytes to a temporary folder, so the hashes are those of the evidence;
2. sets the file's modified time to the original file's (the browser sends `lastModified`), so the timestamp check still works;
3. runs `analyse()` on every file and returns the same HTML case report, shown on the page with a **Download report** button.

It only listens on 127.0.0.1 (nothing leaves the machine), strips folder names from file names, rejects uploads over 300 MB, and deletes the temporary folder afterwards.

### Demo evidence: `make_demo()`
| File | What was done to it | Expected detection |
| --- | --- | --- |
| `original.jpg` | Forest coast photo with "Canon EOS 1500D" EXIF and a matching preview | CLEAN |
| `tampered.jpg` | Street photo; a bicycle from another photo, scaled to 210x120 and saved at quality 70, pasted at (100,420); `Software` = Adobe Photoshop 25.0, changed a week after capture, old preview kept | Editing software + edited region + modified after capture + thumbnail MISMATCH |
| `cloned.jpg` | Flower photo; cluster (340,120)-(530,300) copied into the sky at (700,40), fresh preview, EXIF untouched | Copy-move only |
| `truncated.jpg` | First half of the photo only (interrupted download) | End marker missing, cannot decode |
| `corrupted_header.jpg` | First 16 bytes zeroed | Unknown file signature, cannot decode |
| `broken_data.jpg` | 400 random bytes in the middle of the image data (bad sector) | Corrupted image data (invalid marker) |
| `comment.jpg` | "password for the drive: tiger@123" in a JPEG comment | Text in comment |
| `after_iend.png` | `FLAG{hidden_after_iend}` after the PNG end chunk | 23 bytes hidden text after end marker |
| `embedded_zip.jpg` | Real ZIP (`accounts.txt`) inside an APP15 header segment | ZIP signature inside the image |
| `invoice.jpg` | Windows program (`MZ` header) named `.jpg` | Signature mismatch: EXE |
| `backdated.jpg` | EXIF edit date 5 days before capture date | Modify time BEFORE capture |
| `gps.jpg` | Santorini photo, GPS 36 27' 42.5" N, 25 22' 31.1" E | GPS present, shown as `36.461806, 25.375306` |
| `cropped.jpg` | River photo cropped to 640x640, preview still the full 3:2 frame | Thumbnail aspect ratio differs |
| `stripped.jpg` | Saved with no EXIF (like WhatsApp) | CLEAN (missing EXIF is only a note) |
| `holiday.jpg` | A fake ZIP appended after the JPEG | 60 bytes hidden ZIP data |
| `stego.png` | "Meet at dock 7, 11pm" hidden in red LSBs | LSB message |
| `notes.txt` | A PNG renamed to `.txt` | Signature MISMATCH |

Every sample starts from a different real photo in `8_ImageForensics/photos/` (17 Unsplash photos, 960x640, credits in `photos/CREDITS.md`). They are stored in the project so the demo works offline. `self_check()` asserts all of these. Pillow cannot write an EXIF preview, so `exif_bytes()` builds the EXIF with Pillow and links the preview in by hand (IFD1 with tags `0x0201` offset and `0x0202` length).

## How to Run and Expected Output

```bash
pip install pillow numpy
python LP4/CSDF/8_ImageForensics/image_forensics.py --demo       # create samples and analyse
python LP4/CSDF/8_ImageForensics/image_forensics.py photo.jpg    # your own image
python LP4/CSDF/8_ImageForensics/image_forensics.py --ui           # drag-and-drop page at http://127.0.0.1:8000
```
Reports (`<file>_report.txt`), ELA images and the HTML case report (`report.html`) go to `8_ImageForensics/reports/`.

Real output (trimmed):

```
IMAGE FORENSIC REPORT: tampered.jpg
Generated on: 2026-11-04 13:36:32
Modified  : 2026-11-04 13:36:32
Accessed  : 2026-11-04 13:36:32
Signature : JPEG (matches extension)
Software: Adobe Photoshop 25.0
Max error difference  : 19
Average block error   : 1.059
Suspicious blocks     : 37 of 2400 (1.54%)
Tampering suspicion   : MEDIUM - localised regions differ (possible paste/clone); inspect the ELA image
Possible edited region at (128,432)-(304,528), 37 blocks
Modified after capture: taken 2026-10-15 09:30:00, changed 2026-10-22 09:30:00
Thumbnail : MISMATCH: preview differs from image (max cell difference 99)
SUSPICIOUS:
  - Image was processed by editing software: Adobe Photoshop 25.0
  - Modified after capture: taken 2026-10-15 09:30:00, changed 2026-10-22 09:30:00
  - EXIF thumbnail MISMATCH: preview differs from image (max cell difference 99)
  - Possible edited region at (128,432)-(304,528), 37 blocks

IMAGE FORENSIC REPORT: cloned.jpg
Thumbnail : matches image (max cell difference 14)
Copy-move: regions (700, 40, 890, 220) and (340, 120, 530, 300) are identical (7096 matching blocks)

IMAGE FORENSIC REPORT: holiday.jpg
Appended  : 60 bytes of hidden ZIP data after end-of-image marker

IMAGE FORENSIC REPORT: stego.png
Hidden message found: "Meet at dock 7, 11pm"

IMAGE FORENSIC REPORT: notes.txt
Signature : PNG (MISMATCH: extension '.txt' but content is PNG)

SUMMARY
17 files: original.jpg and stripped.jpg CLEAN, the other 15 SUSPICIOUS
HTML case report: .../8_ImageForensics/reports/report.html
Self-check passed: every planted artefact was detected; original and stripped are clean.
```
The bicycle was pasted over (100,420)-(310,540); the detected region (128,432)-(304,528) lies inside it (block alignment and neighbour smoothing trim the edges). The flowers were copied from (340,120)-(530,300) to (700,40); the two detected boxes are exactly those regions. Open `reports/report.html` to see both regions boxed.

## Related Concepts and Real-World Tools

- **ExifTool** (the standard metadata reader), **Jeffrey's Exif Viewer**.
- **FotoForensics, Forensically (29a.ch), Ghiro, Amped Authenticate, Adobe's content credentials (C2PA)** for ELA, clone detection and provenance.
- **StegHide, OpenStego, zsteg, StegExpose, Stegsolve:** hide or detect steganography.
- **Autopsy / FTK:** file-signature analysis and hashing in a full case.
- **Hash tools:** `sha256sum`, HashCalc; **NSRL** database of known-good file hashes, and **PhotoDNA** for known illegal images.
- **Deepfakes / AI generated images** need other detectors; ELA is not reliable for them.
- **Legal:** IT Act 2000 Section 65B (Evidence Act)/Section 63 BSA 2023 for admissibility of electronic records, Section 66E (privacy violation, capturing images), Section 67 and 67A/67B (obscene / child abuse material), Section 66D / 66C for fake image fraud, Section 43. Hash values and a chain of custody support admissibility.

## Viva Questions

1. **What is digital image forensics and what does the tool check?** Examining an image to establish authenticity and origin. The tool checks file timestamps, hashes, file signature, EXIF, appended data, LSB steganography and ELA.
2. **Why hash an image evidence file?** To prove it has not changed since acquisition; any alteration changes the hash. SHA-256 is preferred over MD5/SHA-1.
3. **What is a magic number and how does it expose a disguised file?** The first bytes that identify the format. `notes.txt` starting with the PNG signature proves a renamed PNG.
4. **What is EXIF and what can it reveal?** Metadata stored in the image: camera model, date/time, GPS, software. It can show the editing program or location, but it can be edited or stripped.
5. **How can data be hidden after an image's end marker?** Viewers stop at `FF D9` (JPEG) or `IEND` (PNG), so appended bytes such as a ZIP stay unseen. The tool measures bytes past the marker.
6. **Explain LSB steganography.** Message bits replace the lowest bit of pixel values, changing colour imperceptibly. Extraction reads those bits and the tool reports them if they form printable text.
7. **Why does LSB need PNG rather than JPEG?** PNG is lossless so the bits survive; JPEG's lossy compression changes pixel values and destroys the hidden bits.
8. **Explain Error Level Analysis.** Re-save the JPEG at a known quality and compare. Regions with a different compression history (pasted patches) show a different error level.
9. **What are the limitations of ELA?** It gives hints, not proof: sharp edges, text and already re-saved images give false positives, and a careful forger can re-compress the whole image.
10. **Steganography vs cryptography?** Cryptography hides the content of a message; steganography hides that a message exists. They are often combined.
11. **What is an EXIF thumbnail mismatch?** The camera's small preview stored in EXIF no longer matches the main image, because an editor changed the image but kept the old preview. A different aspect ratio suggests cropping.
12. **Which timestamps does the tool compare?** EXIF `DateTimeOriginal` (capture), EXIF `DateTime` (last change) and the file's modified time. Change after capture means editing; change before capture or a future date means forged metadata.
13. **What is copy-move forgery and why does ELA miss it?** A region copied within the same image. The copy has the same compression history as its surroundings, so ELA shows nothing unusual.
14. **How does the tool detect copy-move?** A block starts at every pixel; each is described by its 4x4 average brightness, the blocks are sorted so similar ones are adjacent, and the shift between matching pairs is counted. Hundreds of pairs with the same shift mean a cloned region; repeated textures give scattered shifts.
15. **Why skip flat blocks and nearby matches?** Flat areas (sky, walls) and neighbouring blocks look alike naturally and would cause false alarms.
16. **How does the tool detect a corrupted JPEG?** Missing end marker (truncated), unknown signature (wiped header), or invalid `FF xx` markers inside the compressed data (random damage), plus Pillow failing to decode it.
17. **Where else can data hide in an image besides LSB and after the end marker?** In comments (JPEG COM, PNG tEXt) and in unused header segments such as APP15. File carving (searching for signatures) finds embedded files.
18. **How accurate is the tool and how were thresholds chosen?** On 24 real photos with pastes and clones added: 0 false alarms, 18/24 pastes (ELA) and 19/24 clones found. Thresholds were tuned on that set; ELA misses large pastes and copy-move misses clones of flat areas.
19. **Why divide the ELA error by texture?** Detailed areas always re-compress with more error than smooth ones, so plain ELA flags textures. Dividing by the block's texture leaves mainly the compression history.
