# CSDF

## Cyber Security and Digital Forensics Mini Projects

Python implementations of the Group 2 mini projects (8–11). Each tool can create its own sample evidence (including tampered copies), analyse it, write reports, and check that every planted problem was detected.

```bash
pip install -r LP4/CSDF/requirements.txt
```

| # | Mini Project | Run | What it detects |
| --- | --- | --- | --- |
| 8 | Digital forensics of images | `python LP4/CSDF/8_ImageForensics/image_forensics.py --demo` | Hashes, renamed files (magic bytes), EXIF metadata and editing software, data hidden after the end of the image, LSB steganography, edited regions (Error Level Analysis) |
| 9 | Digital forensics of audio | `python LP4/CSDF/9_AudioForensics/audio_forensics.py --demo` | Hashes, header consistency, metadata and editing software, splices (sample jumps or background-noise change), erased sections (digital silence), LSB steganography, waveform image |
| 10 | Digital forensics of video | `python LP4/CSDF/10_VideoForensics/video_forensics.py --demo` | Hashes, renamed files, codec/FPS/encoder metadata, deleted frames (motion jump), duplicated/frozen frames, evidence frame images |
| 11 | Cyber crime analysis and comparison of techniques | `python LP4/CSDF/11_CyberCrimeAnalysis/forensic_system.py` | Insider data-theft case: acquisition, hashing, HMAC chain of custody, write blocking, AES encryption, access control and backups, attacked and scored on Confidentiality, Integrity and Availability |

To analyse your own files instead of the demo, pass them as arguments:

```bash
python LP4/CSDF/8_ImageForensics/image_forensics.py photo.jpg
python LP4/CSDF/9_AudioForensics/audio_forensics.py call.wav
python LP4/CSDF/10_VideoForensics/video_forensics.py cctv.mp4
```

Reports are written to a `reports/` folder next to each script. Audio must be 16-bit PCM WAV; convert other formats with `ffmpeg -i in.mp3 -acodec pcm_s16le out.wav`. For video, installing ffmpeg also lets the tool read encoder and creation-time tags.
