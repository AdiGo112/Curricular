# Assignment 10 (Mini Project): Digital Forensics of Video

## Aim

Design and develop a tool for digital forensics of video.

## Theory and Fundamentals

### What a video file is
A video is a sequence of still **frames** shown quickly (e.g. 25 frames per second, **FPS**), usually with an audio track, packed in a **container** (MP4, AVI, MKV) and compressed with a **codec** (H.264, MPEG-4, H.265).

| Term | Meaning |
| --- | --- |
| **Frame** | One still image |
| **FPS** | Frames per second; duration = frames / FPS |
| **Resolution** | Width x height in pixels |
| **Container** | File wrapper holding video, audio, subtitles and metadata (MP4 has an `ftyp` box near the start; AVI starts with `RIFF`; MKV/WebM with `1A 45 DF A3`) |
| **Codec** | Compression method (shown by a FourCC code such as `avc1`, `mp4v`, `FMP4`) |
| **I / P / B frames** | Key frames store the whole picture; P/B frames store only changes. Cutting in a compressed video forces re-encoding, which leaves traces |
| **Metadata** | Encoder, creation time, device, GPS, software |

### Why video forensics?
CCTV, dashcam, mobile and social-media videos are key evidence. Questions: *Is it genuine? Was part removed or repeated? Which software exported it? When and on what device was it created?*

### Common video tampering
| Tampering | What it looks like |
| --- | --- |
| **Frame deletion / cutting** | The scene "jumps": an object moves unnaturally far between two consecutive frames; timestamps or counters skip |
| **Frame duplication / freezing** | The same frame repeated so that nothing seems to happen, hiding an event |
| **Insertion / splicing** | Frames from another video added; compression and noise differ |
| **Re-encoding / editing** | Encoder metadata of an editor (Premiere, DaVinci, CapCut) replaces the camera's |
| **Disguising** | An MP4 renamed `.pdf` |
| **Deepfakes** | AI-generated faces/voices, needs specialised detectors |

### Detection principles used in this project
- **Motion continuity:** between consecutive frames of normal footage, roughly the same fraction of pixels changes. A sudden large jump means frames are missing.
- **Zero change:** several consecutive frames with practically no pixel change means repeated (frozen) frames. (Real cameras always have a little sensor noise.)
- **Integrity:** hash of the file; **signature** check for a disguised file; **metadata** for software traces.

### Other methods (not coded)
Double-compression and GOP (group of pictures) analysis, PRNU sensor noise to identify the camera, frame-rate/timestamp analysis, visible clock or shadow consistency, optical-flow analysis, audio-video sync.

## How the Code Works

File: `10_VideoForensics/video_forensics.py` (OpenCV `cv2` + NumPy; `ffprobe` optional).

### Thresholds
```python
PIXEL_CHANGE = 15      # a pixel "changed" if its brightness moved by more than this
JUMP_FACTOR = 4.0      # motion > 4x the typical motion = deleted frames
FREEZE_DIFF = 0.05     # less than 0.05 % pixels changed = duplicate frame
FREEZE_MIN = 10        # at least this many duplicate frames in a row = freeze
```

### Steps in `analyse(path, out_dir)`
1. **Hashes:** `hashes()` reads the file in 1 MB chunks (works for large videos) and returns MD5 and SHA-256.
2. **Signature:** `check_signature()` compares bytes with the `SIGNATURES` table (MP4 `ftyp` at offset 4, AVI `RIFF`, MKV/WebM) and the extension; a mismatch is suspicious.
3. **Metadata:** OpenCV gives resolution, FPS and codec FourCC. If `ffprobe` is installed, `ffprobe_tags()` adds container tags (encoder, creation time) and the tool flags editors such as premiere, after effects, davinci, filmora, capcut, kinemaster, imovie, vegas. Without ffmpeg it prints a hint.
4. **Frame differences:** `frame_differences()` decodes every frame, resizes to 320x180, converts to grey and records, for each pair of neighbouring frames, the **percentage of pixels whose brightness changed by more than 15**.
```python
gray = cv2.cvtColor(cv2.resize(frame, (320, 180)), cv2.COLOR_BGR2GRAY).astype(np.float32)
if prev is not None:
    diffs.append(100 * float(np.mean(np.abs(gray - prev) > PIXEL_CHANGE)))
```
5. **Frame deletion:** `find_jumps()` takes the median of all "moving" differences (above 0.05 %) as typical motion; any difference above 4x that is reported as an abrupt jump at that frame index (needs at least 5 moving pairs).
6. **Freeze:** `find_freezes()` finds runs of differences below 0.05 % that are at least 10 frames long.
7. **Evidence frames:** `save_frames()` stores PNGs of the frames before and after each suspicious point (`<name>_frame<N>.png`).

The report also compares decoded frame count with the count declared in the header, and prints the duration.

### Demo clips: `make_demo()`
`cctv_frames()` draws 150 frames of a "person" (circle) walking across a room with a camera clock `CAM-02 21:14:SS.FF` written on each frame; clips are written at 25 FPS, 640x360 with the `mp4v` codec.

| File | Manipulation | Expected |
| --- | --- | --- |
| `original.mp4` | none | CLEAN |
| `deleted.mp4` | frames 60-99 (40 frames, 1.6 s) removed | Abrupt jump at frame 60 |
| `frozen.mp4` | frame 60 repeated for 40 frames | Freeze frames 60-99 |
| `minutes.pdf` | copy of the MP4 renamed | Signature MISMATCH |

## How to Run and Expected Output

```bash
pip install opencv-python numpy
python LP4/CSDF/10_VideoForensics/video_forensics.py --demo        # create CCTV clips and analyse
python LP4/CSDF/10_VideoForensics/video_forensics.py cctv.mp4      # your own video
```
Optional: install ffmpeg so `ffprobe` can read encoder and creation-time tags. Reports and evidence images go to `10_VideoForensics/reports/`.

Real output (trimmed):

```
VIDEO FORENSIC REPORT: deleted.mp4
Resolution: 640x360   FPS: 25.00   Codec: FMP4
Frames    : 110 decoded (header says 110), duration 4.40 s
Abrupt jump at frame 60 (2.40 s): frames deleted or clip cut
  evidence: ...\reports\deleted_frame59.png
  evidence: ...\reports\deleted_frame60.png

VIDEO FORENSIC REPORT: frozen.mp4
Abrupt jump at frame 100 (4.00 s): frames deleted or clip cut
Frames 60-99 identical (1.60 s freeze): event may be hidden

VIDEO FORENSIC REPORT: minutes.pdf
Signature : MP4/MOV (MISMATCH: extension '.pdf' but content is MP4/MOV)

Self-check passed: every planted artefact was detected, original is clean.
```
Observations: `deleted.mp4` is 110 frames long (150 - 40). In `frozen.mp4` the end of the freeze is also an abrupt motion jump (the person moves from the frozen position to where the video resumes), so both detectors fire, which is correct. Compare `deleted_frame59.png` and `deleted_frame60.png`: the person "teleports" and the on-screen clock jumps. The sample metadata shows `encoder: Lavf61.7.100` (from FFmpeg's libraries, as the clips were produced by OpenCV), not a camera, which is normal for synthetic files.

## Related Concepts and Real-World Tools

- **FFmpeg / `ffprobe`, MediaInfo:** extract frames, metadata, codec details.
- **VLC, Avidemux:** frame-by-frame playback.
- **Amped FIVE / Amped Authenticate, Cognitech, Input-Ace, Kinesense:** professional CCTV enhancement and authentication.
- **Autopsy / FTK** for the whole case; **Magnet Video Investigator**.
- **InVID-WeVerify:** browser plug-in to check social-media videos, key-frame reverse search.
- **Deepfake detection:** Microsoft Video Authenticator, Sensity, research datasets (FaceForensics++).
- **DVR/CCTV forensics:** extract from the DVR with a write blocker, check the DVR clock offset against real time.
- **Legal:** electronic records admissible with Section 65B certificate (Indian Evidence Act, now Section 63 BSA 2023); IT Act Section 66E (privacy), 67/67A/67B (obscene content), 65 (tampering with source documents), 66D (impersonation, deepfake fraud). Preserve the original, hash it, work on a copy.

## Viva Questions

1. **What are FPS, codec and container?** FPS is frames per second; a codec compresses the video (H.264, MPEG-4); a container (MP4, AVI, MKV) packs video, audio and metadata into one file.
2. **How does the tool detect deleted frames?** It measures the percentage of changed pixels between every pair of frames. A jump greater than 4 times the typical motion means frames are missing.
3. **How does it detect a frozen or duplicated sequence?** Runs of at least 10 consecutive frames with less than 0.05 % pixel change are reported as a freeze; real cameras always show a little noise.
4. **Why were frames before and after the jump saved as images?** They are visual evidence for the report (e.g. the person appears at a different place, the clock skips).
5. **What does the file signature check show?** Whether the real format (MP4 `ftyp`, AVI `RIFF`, MKV `1A 45 DF A3`) matches the extension; `minutes.pdf` was really an MP4.
6. **What metadata is useful in video forensics?** Resolution, FPS, codec, encoder, creation time, device and GPS. An editor's name instead of the camera suggests re-export.
7. **Why would frames be duplicated by a criminal?** To hide an event while keeping the video's length and timestamps looking continuous.
8. **Why is a sudden big change not always tampering?** A real scene change, fast motion or a light flash also causes it, so findings are indicators that need human review of the evidence frames.
9. **What other techniques exist that this tool does not use?** Double-compression/GOP analysis, PRNU camera fingerprinting, timestamp and audio-sync analysis, deepfake detectors.
10. **How do you keep video evidence admissible?** Work on a copy, record MD5/SHA-256 of the original, maintain a chain of custody, document each tool and step, and provide the Section 65B certificate.
