# Assignment 9 (Mini Project): Digital Forensics of Audio

## Aim

Design and develop a tool for digital forensics of audio.

## Theory and Fundamentals

### Digital audio basics
Sound is a continuous wave. A computer stores it by **sampling**: measuring the wave's height many times per second.
- **Sample rate:** measurements per second (16,000 Hz for phone-quality speech, 44,100 Hz for CD).
- **Bit depth:** bits per sample. **16-bit** gives values from -32768 to +32767.
- **Channels:** mono = 1, stereo = 2.
- **PCM (Pulse Code Modulation):** raw, uncompressed samples. WAV usually holds PCM. MP3/AAC are **lossy compressed** formats.

### The WAV file (RIFF container)
A WAV file is a **RIFF** file: the header `RIFF <size> WAVE`, followed by **chunks**, each `ID (4 bytes) + size (4 bytes) + data`.

| Chunk | Content |
| --- | --- |
| `fmt ` | Format: PCM, channels, sample rate, bits |
| `data` | The samples |
| `LIST` / `INFO` | Optional metadata: title (`INAM`), artist (`IART`), creation date (`ICRD`), software (`ISFT`), comment (`ICMT`) |

The RIFF size field should equal *file size - 8*. If not, the file was **truncated or extra data was appended**.

### What audio forensics tries to establish
- **Authenticity:** has the recording been cut, joined (**splicing**), or has a part been erased/muted?
- **Origin:** which device or software made or saved it (metadata).
- **Content:** enhancement, speaker identification, transcription; detecting hidden data.

### Common tampering and how it shows
| Tampering | Trace left behind |
| --- | --- |
| **Splicing** (cut and join, insert from another recording) | A sudden **jump** between neighbouring samples at the joint, and/or a **change in background noise** (different room/microphone) |
| **Deletion / muting** | A run of **exact digital silence** (all zero samples). Real rooms always have some noise, so perfect zeros are artificial |
| **Re-saving in an editor** | `ISFT` metadata such as Audacity, Adobe Audition |
| **Renamed file** | WAV data in a file called `.mp3` |
| **Hidden message (LSB steganography)** | Lowest bit of each sample carries text, which is inaudible |

### ENF analysis (concept)
**Electric Network Frequency:** mains electricity hums at 50 Hz in India (60 Hz in the US) and the frequency wobbles slightly over time. Recordings made near mains equipment capture this hum. Comparing the recorded hum pattern with a power-grid reference database dates a recording and reveals edits, because a cut or inserted section breaks the pattern. This tool does **not** implement ENF; it is mentioned as the standard advanced technique.

### Other concepts
- **Waveform and spectrogram:** amplitude vs time and frequency vs time; audio examiners study both.
- **Noise floor:** the level of background noise; it is a "signature" of a room/device.
- **Compression artefacts and double compression** (MP3 re-encoding) indicate processing.
- **Hash** of the file for integrity (see Assignment 8).

## How the Code Works

File: `9_AudioForensics/audio_forensics.py` (NumPy + Pillow + the standard `wave` module). Only **16-bit PCM WAV** is supported.

| # | Function | Technique |
| --- | --- | --- |
| 1 | in `analyse` | MD5 and SHA-256 of the file |
| 2 | `header_checks`, `read_chunks` | Checks `RIFF`/`WAVE`, extension, and `riff_size + 8 == file size` |
| 3 | `read_info` | Parses `LIST`/`INFO` sub-chunks; flags `Software` containing audacity, audition, fl studio, garageband, wavepad, ocenaudio |
| 4a | `find_jumps` | Splice point as a sudden sample jump |
| 4b | `find_noise_changes` | Splice as a change in background-noise level |
| 5 | `find_digital_silence` | Erased / muted section |
| 6 | `lsb_extract` | Hidden text in sample LSBs |
| 7 | `draw_waveform` | Waveform PNG with suspicious spans boxed in red |

### Thresholds
```python
FRAME_MS = 100           # noise level is measured per 100 ms frame
NOISE_Z = 3.0            # frame is suspicious if noise level z-score > 3
JUMP_FACTOR = 6.0        # sample jump > 6x the 99.9th percentile = splice
SILENCE_MS = 200         # this many ms of exact zeros = deleted section
```

### `find_jumps`: sample-to-sample jumps
Take the absolute difference between neighbouring samples; the "normal" size is the 99.9th percentile. Any difference larger than 6 times that is a splice candidate; jumps closer than 0.5 s are merged.

### `find_noise_changes`: background-noise level
The **second difference** (`np.diff(x, 2)`) acts as a high-pass filter that removes the slowly changing voice/tone and leaves mostly noise. The RMS of this residual is computed per 100 ms frame, converted to a log scale, and each frame gets a **robust z-score** using the median and the MAD (median absolute deviation x 1.4826). Runs of at least 3 abnormal frames (300 ms) are reported as a segment.

### `find_digital_silence`
Marks samples equal to 0 and finds runs; a run of 200 ms or more (3200 samples at 16 kHz) is reported.

### LSB steganography
```python
y[: len(bits)] = (y[: len(bits)] & ~1) | bits       # hide
raw = np.packbits((x[: max_chars * 8] & 1).astype(np.uint8)).tobytes()   # extract
```
Same idea as images, applied to the sample values; text must be at least 4 printable characters ending with a zero byte.

### Demo recordings: `make_demo()`
`recording()` synthesises a speech-like signal (changing pitch tones + syllable envelope + room noise). Files created:

| File | Manipulation | Expected |
| --- | --- | --- |
| `original.wav` | 6 s, metadata "Voice Recorder 3.1" | CLEAN |
| `spliced.wav` | 1.5 s from a *noisier* recording inserted at 2.0 s, saved by "Audacity 3.4" | Editing software + noise change 2.0-3.5 s |
| `muted.wav` | 1 s erased to zeros at 3.0 s | Digital silence 3.00-4.00 s |
| `stego.wav` | "Transfer 5 lakh on Friday" hidden in LSBs | LSB message |
| `song.mp3` | A WAV file renamed to `.mp3` | Extension MISMATCH |

## How to Run and Expected Output

```bash
pip install numpy pillow
python LP4/CSDF/9_AudioForensics/audio_forensics.py --demo        # creates samples, analyses them
python LP4/CSDF/9_AudioForensics/audio_forensics.py call.wav      # your own recording
ffmpeg -i input.mp3 -acodec pcm_s16le output.wav                  # convert other formats first
```
Reports and `*_waveform.png` images are saved in `9_AudioForensics/reports/`.

Real output (trimmed):

```
AUDIO FORENSIC REPORT: spliced.wav
Software: Audacity 3.4
Background noise changes between 2.0 s and 3.5 s (inserted segment?)
SUSPICIOUS:
  - Saved by editing software: Audacity 3.4
  - Background noise changes between 2.0 s and 3.5 s (inserted segment?)

AUDIO FORENSIC REPORT: muted.wav
Background noise changes between 3.0 s and 4.0 s (inserted segment?)
Exact digital silence 3.00-4.00 s (section erased?)

AUDIO FORENSIC REPORT: song.mp3
Header    : MISMATCH: extension '.mp3' but content is WAV

original.wav CLEAN
Self-check passed: every planted artefact was detected, original is clean.
```
Observations: in the spliced sample, the noise-change detector found the insertion but the jump detector did not fire (no sample jump exceeded the threshold); the muted section is reported twice (as a noise change and as digital silence), which is expected because zeros differ strongly from the noise level around them.

## Related Concepts and Real-World Tools

- **Audacity** (free editor: waveform, spectrogram, noise reduction, analysis), **Adobe Audition**, **Praat** (speech analysis), **Sonic Visualiser**.
- **iZotope RX, Amped DeNoise / Amped Authenticate, Cedar, SIS II:** professional forensic audio enhancement and authentication.
- **FFmpeg / `ffprobe`:** convert formats and read metadata.
- **ENF databases and research tools** for date verification.
- **Speaker identification / voice biometrics**; **deepfake voice detection** is an active research area.
- **MP3 / AAC** "double compression" detection and **codec/bitrate analysis**.
- **Legal:** audio evidence (call recordings, voice notes) is an electronic record under Section 65B Indian Evidence Act (now Section 63 BSA 2023); hash and chain of custody are needed. IT Act Section 66D/66C (voice impersonation fraud), Section 67 (obscene content), Section 69 (interception needs government authorisation).

## Viva Questions

1. **What is PCM and what is a WAV file?** PCM is uncompressed digital audio (raw samples). WAV is a RIFF container that normally holds PCM, with `fmt `, `data` and optional `LIST/INFO` chunks.
2. **What do sample rate and bit depth mean?** Sample rate is how many measurements per second; bit depth is how finely each is stored. The demo uses 16,000 Hz, 16-bit, mono.
3. **What is audio splicing and how does the tool detect it?** Cutting and joining or inserting audio from another recording. The tool looks for sudden sample jumps and for segments whose background-noise level differs from the rest.
4. **Why does perfect silence indicate deletion?** Real recordings always contain room and electronic noise; runs of exact zero samples (200 ms or more) mean the section was erased or muted digitally.
5. **What is the second difference used for?** It removes the slowly varying voice signal and leaves mostly background noise, so noise levels can be compared per 100 ms frame.
6. **What metadata can reveal tampering?** The `INFO` chunk may show the recorder or editing software (e.g. Audacity), and the creation date; a mismatch with the claimed device is a clue.
7. **How does the header check find a truncated or padded file?** The RIFF header stores the file size minus 8; if it does not match the real size, bytes were cut or appended.
8. **What is ENF analysis?** Matching the faint mains hum (50 Hz in India) captured in a recording with grid records, to date it and detect edits. It is not implemented here.
9. **How is data hidden in audio with LSB?** Each message bit replaces the lowest bit of a sample, a change too small to hear. Extraction reads the lowest bits and checks for readable text.
10. **What are the limits of this tool?** It supports only 16-bit PCM WAV, uses simple statistical thresholds, and cannot detect careful edits that match noise levels or those made before lossy compression.
