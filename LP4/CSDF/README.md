# CSDF: Cyber Security and Digital Forensics (410244(C))

**Study notes:** [`Explanations/`](Explanations/README.md) has one file per assignment with theory, a code walkthrough, how to run it and viva questions.

```bash
pip install -r LP4/CSDF/requirements.txt
```

Every program has a demo mode that creates its own sample data, runs, and ends with a self-check. Run them all with `python LP4/CSDF/run_all.py`, or in Docker (see the bottom of this page).

## Group 1: Assignments

| # | Assignment | Run | What it does |
| --- | --- | --- | --- |
| 1 | Track emails and investigate email crimes (header analysis) | `python LP4/CSDF/1_EmailHeaderAnalysis/email_header_analyzer.py --demo` | Traces the route hop by hop, finds the originating IP, reads SPF/DKIM/DMARC, flags spoofing (Return-Path / Reply-To / Message-ID mismatch, fake display names, deceptive links), gives a risk score |
| 2 | Generate and verify a CAPTCHA image | `python LP4/CSDF/2_CAPTCHA/captcha.py` (`--test` for the self-test) | Distorted text with noise and waves; answer stored only as an HMAC; case-insensitive, 2-minute expiry, 3 attempts, one-time use |
| 3 | Detect and prohibit Wi-Fi password cracking (IEEE 802.11) | `python LP4/CSDF/3_WiFiIntrusionDetection/wifi_guard.py --simulate` | Reads hostapd events: brute force, MAC rotation, deauth attack, unknown device; blocks the MAC and cuts printer access with iptables. The README has the full AP setup |
| 4 | Recover deleted files and deleted partitions | `python LP4/CSDF/4_DataRecovery/recover.py --demo` | Rebuilds the partition table from boot-sector signatures, undeletes FAT32 files (0xE5 entries), carves JPEG/PNG/PDF/ZIP; hashes match the originals |
| 5 | Log capturing and event correlation | `python LP4/CSDF/5_LogCorrelation/log_correlator.py --demo` | UDP syslog collector + 7 correlation rules across SSH, web and firewall logs (port scan → web attack, brute force → login → sudo, exfiltration) |
| 6 | Wireshark / SNORT | `python LP4/CSDF/6_WiresharkSnort/mini_ids.py` | `test_traffic.pcap` with attacks, custom `local.rules`, a mini IDS using the same rules; README has the Wireshark filters and Snort setup |
| 7 | Study of honeypot | `python LP4/CSDF/7_Honeypot/honeypot.py --demo` | Study notes in the README + working low-interaction honeypot (fake SSH, Telnet shell, router login page) |

## Group 2: Mini Projects

Each tool can create its own sample evidence (including tampered copies), analyse it, write reports, and check that every planted problem was detected.

| # | Mini Project | Run | What it detects |
| --- | --- | --- | --- |
| 8 | Digital forensics of images | `python LP4/CSDF/8_ImageForensics/image_forensics.py --demo` | Hashes, renamed files (magic bytes), EXIF metadata and editing software, data hidden after the end of the image, LSB steganography, edited regions (Error Level Analysis) |
| 9 | Digital forensics of audio | `python LP4/CSDF/9_AudioForensics/audio_forensics.py --demo` | Hashes, header consistency, metadata and editing software, splices (sample jumps or background-noise change), erased sections (digital silence), LSB steganography, waveform image |
| 10 | Digital forensics of video | `python LP4/CSDF/10_VideoForensics/video_forensics.py --demo` | Hashes, renamed files, codec/FPS/encoder metadata, deleted frames (motion jump), duplicated/frozen frames, evidence frame images |
| 11 | Cyber crime analysis and comparison of techniques | `python LP4/CSDF/11_CyberCrimeAnalysis/forensic_system.py` | Insider data-theft case: acquisition, hashing, HMAC chain of custody, write blocking, AES encryption, access control and backups, attacked and scored on Confidentiality, Integrity and Availability |

To analyse your own files instead of the demo, pass them as arguments:

```bash
python LP4/CSDF/1_EmailHeaderAnalysis/email_header_analyzer.py mail.eml
python LP4/CSDF/4_DataRecovery/recover.py usb.img
python LP4/CSDF/6_WiresharkSnort/mini_ids.py capture.pcap
python LP4/CSDF/8_ImageForensics/image_forensics.py photo.jpg
python LP4/CSDF/9_AudioForensics/audio_forensics.py call.wav
python LP4/CSDF/10_VideoForensics/video_forensics.py cctv.mp4
```

Audio must be 16-bit PCM WAV; convert other formats with `ffmpeg -i in.mp3 -acodec pcm_s16le out.wav`. For video, installing ffmpeg also lets the tool read encoder and creation-time tags.

## Docker

The whole subject runs in one small Python image (no GUI needed):

```bash
cd LP4/CSDF
docker build -t csdf .
docker run --rm csdf                                        # every demo + self-check (11 programs)

# single tools
docker run --rm csdf python 1_EmailHeaderAnalysis/email_header_analyzer.py --demo
docker run --rm -it csdf python 2_CAPTCHA/captcha.py --test

# your own evidence: mount a folder
docker run --rm -v "$PWD/evidence:/evidence" csdf python 8_ImageForensics/image_forensics.py /evidence/photo.jpg

# services that listen on the network
docker run --rm -p 2222:2222 -p 2323:2323 -p 8080:8080 csdf python 7_Honeypot/honeypot.py --public
docker run --rm -p 5514:5514/udp csdf python 5_LogCorrelation/log_correlator.py --listen 5514
```

Assignment 3's `--enforce` mode (hostapd / iptables) needs a real Linux access point and cannot run in a container. Use `--simulate` in Docker.
