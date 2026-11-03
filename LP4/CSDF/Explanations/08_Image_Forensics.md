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

### Other image forensic ideas (not coded)
Clone/copy-move detection, PRNU camera noise fingerprint (identify the camera), thumbnail mismatch, lighting/shadow inconsistencies, reverse image search.

## How the Code Works

File: `8_ImageForensics/image_forensics.py` (Pillow + NumPy). `analyse(path, out_dir)` runs six checks and collects anything unusual in a `suspicious` list; the file is `CLEAN` if the list is empty.

| # | Function | What it does |
| --- | --- | --- |
| 1 | `file_hashes` | MD5, SHA-1, SHA-256 of the file bytes |
| 2 | `check_signature` | Compares leading bytes with the `SIGNATURES` table and the extension; reports `MISMATCH` |
| 3 | `read_exif` | Reads EXIF and the GPS block; flags `Software` containing photoshop/gimp/paint.net/lightroom/snapseed/picsart/canva, GPS present, or EXIF missing |
| 4 | `appended_data` | JPEG: bytes after the last `FF D9`; PNG: after `IEND` + 4 CRC bytes; reports size and type of the hidden blob |
| 5 | `lsb_extract` | Reads the lowest bit of the first 4000 red-channel values, packs them into bytes, stops at a 0 byte; reports only if the result is at least 4 printable ASCII characters |
| 6 | `error_level_analysis` | ELA (JPEG only), see below |

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
3. Each block gets a **z-score** (distance from the mean in standard deviations). Blocks can be abnormally high *or* low, so the absolute value is used.
4. Each block is averaged with its 8 neighbours so isolated noisy blocks cancel while a real pasted region stays strong.
5. Blocks with `|z| > 3.0` (`ELA_THRESHOLD`) are reported as a bounding box. The source comment notes this is a simple threshold to be tuned per camera.

### Demo evidence: `make_demo()`
| File | What was done to it | Expected detection |
| --- | --- | --- |
| `original.jpg` | Synthetic "Canon EOS 1500D" photo with EXIF | CLEAN |
| `tampered.jpg` | A patch saved at JPEG quality 40 pasted in, `Software` = Adobe Photoshop 25.0 | Editing software + edited region |
| `holiday.jpg` | A fake ZIP appended after the JPEG | 60 bytes hidden ZIP data |
| `stego.png` | "Meet at dock 7, 11pm" hidden in red LSBs | LSB message |
| `notes.txt` | A PNG renamed to `.txt` | Signature MISMATCH |

`self_check()` asserts all of these.

## How to Run and Expected Output

```bash
pip install pillow numpy
python LP4/CSDF/8_ImageForensics/image_forensics.py --demo       # create samples and analyse
python LP4/CSDF/8_ImageForensics/image_forensics.py photo.jpg    # your own image
```
Reports (`<file>_report.txt`) and ELA images go to `8_ImageForensics/reports/`.

Real output (trimmed):

```
IMAGE FORENSIC REPORT: tampered.jpg
Signature : JPEG (matches extension)
Software: Adobe Photoshop 25.0
Possible edited region at (320,192)-(400,256), 17 blocks
SUSPICIOUS:
  - Image was processed by editing software: Adobe Photoshop 25.0
  - Possible edited region at (320,192)-(400,256), 17 blocks

IMAGE FORENSIC REPORT: holiday.jpg
Appended  : 60 bytes of hidden ZIP data after end-of-image marker

IMAGE FORENSIC REPORT: stego.png
Hidden message found: "Meet at dock 7, 11pm"

IMAGE FORENSIC REPORT: notes.txt
Signature : PNG (MISMATCH: extension '.txt' but content is PNG)

SUMMARY
holiday.jpg SUSPICIOUS | notes.txt SUSPICIOUS | original.jpg CLEAN | stego.png SUSPICIOUS | tampered.jpg SUSPICIOUS
Self-check passed: every planted artefact was detected, original is clean.
```
The demo pasted a 120x90 patch at (300,180), i.e. the area (300,180)-(420,270); the detected region (320,192)-(400,256) lies inside it (block alignment and neighbour smoothing trim the edges). Open `reports/tampered_ELA.png` to see the bright patch.

## Related Concepts and Real-World Tools

- **ExifTool** (the standard metadata reader), **Jeffrey's Exif Viewer**.
- **FotoForensics, Forensically (29a.ch), Ghiro, Amped Authenticate, Adobe's content credentials (C2PA)** for ELA, clone detection and provenance.
- **StegHide, OpenStego, zsteg, StegExpose, Stegsolve:** hide or detect steganography.
- **Autopsy / FTK:** file-signature analysis and hashing in a full case.
- **Hash tools:** `sha256sum`, HashCalc; **NSRL** database of known-good file hashes, and **PhotoDNA** for known illegal images.
- **Deepfakes / AI generated images** need other detectors; ELA is not reliable for them.
- **Legal:** IT Act 2000 Section 65B (Evidence Act)/Section 63 BSA 2023 for admissibility of electronic records, Section 66E (privacy violation, capturing images), Section 67 and 67A/67B (obscene / child abuse material), Section 66D / 66C for fake image fraud, Section 43. Hash values and a chain of custody support admissibility.

## Viva Questions

1. **What is digital image forensics and what does the tool check?** Examining an image to establish authenticity and origin. The tool checks hashes, file signature, EXIF, appended data, LSB steganography and ELA.
2. **Why hash an image evidence file?** To prove it has not changed since acquisition; any alteration changes the hash. SHA-256 is preferred over MD5/SHA-1.
3. **What is a magic number and how does it expose a disguised file?** The first bytes that identify the format. `notes.txt` starting with the PNG signature proves a renamed PNG.
4. **What is EXIF and what can it reveal?** Metadata stored in the image: camera model, date/time, GPS, software. It can show the editing program or location, but it can be edited or stripped.
5. **How can data be hidden after an image's end marker?** Viewers stop at `FF D9` (JPEG) or `IEND` (PNG), so appended bytes such as a ZIP stay unseen. The tool measures bytes past the marker.
6. **Explain LSB steganography.** Message bits replace the lowest bit of pixel values, changing colour imperceptibly. Extraction reads those bits and the tool reports them if they form printable text.
7. **Why does LSB need PNG rather than JPEG?** PNG is lossless so the bits survive; JPEG's lossy compression changes pixel values and destroys the hidden bits.
8. **Explain Error Level Analysis.** Re-save the JPEG at a known quality and compare. Regions with a different compression history (pasted patches) show a different error level.
9. **What are the limitations of ELA?** It gives hints, not proof: sharp edges, text and already re-saved images give false positives, and a careful forger can re-compress the whole image.
10. **Steganography vs cryptography?** Cryptography hides the content of a message; steganography hides that a message exists. They are often combined.
