# =========================================================
# MINI PROJECT 9
# Tool for Digital Forensics of Audio
# =========================================================
#
# Checks performed on a WAV recording (evidence):
#
#   1. Hashing (MD5, SHA-256)          -> integrity
#   2. File signature + header check   -> renamed file,
#                                         truncated / padded file
#   3. Metadata (RIFF LIST/INFO chunk) -> recorder, date,
#                                         editing software
#   4. Splice detection                -> sudden jump between
#                                         samples, or a change
#                                         in background noise
#   5. Deleted section detection       -> run of exact digital
#                                         silence (real rooms are
#                                         never perfectly silent)
#   6. LSB steganography               -> text hidden in the
#                                         lowest bit of samples
#   7. Waveform image                  -> suspicious points marked
#
# =========================================================
# HOW TO RUN
# =========================================================
#
#   pip install numpy pillow
#
#   python audio_forensics.py --demo           (creates sample
#                                               recordings and
#                                               analyses them)
#   python audio_forensics.py call.wav         (your own file)
#
# Only 16-bit PCM WAV is supported. Convert other formats:
#   ffmpeg -i input.mp3 -acodec pcm_s16le output.wav
#
# =========================================================

import argparse
import hashlib
import os
import struct
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw

EDITING_SOFTWARE = ["audacity", "audition", "fl studio", "garageband", "wavepad", "ocenaudio"]

FRAME_MS = 100           # noise level is measured per 100 ms frame
NOISE_Z = 3.0            # frame is suspicious if noise level z-score > 3
JUMP_FACTOR = 6.0        # sample jump > 6x the 99.9th percentile = splice
SILENCE_MS = 200         # this many ms of exact zeros = deleted section


# =========================================================
# 1-2. HASHES, SIGNATURE AND RIFF CHUNKS
# =========================================================

def read_chunks(data):
    """Return list of (chunk_id, offset, size) inside a RIFF/WAVE file."""
    chunks = []
    pos = 12
    while pos + 8 <= len(data):
        cid, size = struct.unpack("<4sI", data[pos:pos + 8])
        chunks.append((cid.decode("latin-1"), pos + 8, size))
        pos += 8 + size + (size & 1)
    return chunks


def header_checks(path, data):
    findings = []
    ext = os.path.splitext(path)[1].lower()

    if not (data[:4] == b"RIFF" and data[8:12] == b"WAVE"):
        return ["Not a RIFF/WAVE file"], []
    if ext != ".wav":
        findings.append(f"MISMATCH: extension '{ext}' but content is WAV")

    riff_size = struct.unpack("<I", data[4:8])[0]
    if riff_size + 8 != len(data):
        findings.append(f"Header says {riff_size + 8} bytes but file has {len(data)} "
                        f"(file was cut or extra data appended)")
    return findings, read_chunks(data)


# =========================================================
# 3. METADATA (LIST / INFO)
# =========================================================

INFO_NAMES = {"INAM": "Title", "IART": "Artist", "ICRD": "Created", "ISFT": "Software",
              "ICMT": "Comment", "IENG": "Engineer"}


def read_info(data, chunks):
    info = {}
    for cid, off, size in chunks:
        if cid == "LIST" and data[off:off + 4] == b"INFO":
            pos, end = off + 4, off + size
            while pos + 8 <= end:
                key, n = struct.unpack("<4sI", data[pos:pos + 8])
                value = data[pos + 8:pos + 8 + n].rstrip(b"\x00").decode("latin-1")
                info[INFO_NAMES.get(key.decode(), key.decode())] = value
                pos += 8 + n + (n & 1)
    return info


def write_wav(path, samples, rate, info=None):
    """Write 16-bit mono WAV with an optional LIST/INFO metadata chunk."""
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(samples.astype("<i2").tobytes())
    if not info:
        return
    keys = {v: k for k, v in INFO_NAMES.items()}
    body = b"INFO"
    for name, value in info.items():
        raw = value.encode() + b"\x00"
        raw += b"\x00" * (len(raw) & 1)
        body += keys[name].encode() + struct.pack("<I", len(raw)) + raw
    with open(path, "r+b") as f:
        content = f.read() + b"LIST" + struct.pack("<I", len(body)) + body
        content = content[:4] + struct.pack("<I", len(content) - 8) + content[8:]
        f.seek(0)
        f.write(content)


# =========================================================
# 4. SPLICE DETECTION
# =========================================================

def find_jumps(x, rate):
    """Sudden jumps between neighbouring samples (cut-and-join points)."""
    d = np.abs(np.diff(x.astype(np.float64)))
    normal = np.percentile(d, 99.9)
    idx = np.where(d > JUMP_FACTOR * max(normal, 1))[0]
    times, last = [], -rate
    for i in idx:                         # merge jumps closer than 0.5 s
        if i - last > rate // 2:
            times.append(i / rate)
        last = i
    return times


def find_noise_changes(x, rate):
    """Segments whose background noise differs from the rest of the recording."""
    frame = rate * FRAME_MS // 1000
    n = len(x) // frame
    # 2nd difference removes the speech/tone, leaving mostly background noise
    resid = np.diff(x[: n * frame].astype(np.float64), 2)
    level = np.sqrt(np.mean(np.pad(resid, (0, 2)).reshape(n, frame) ** 2, axis=1))
    level = np.log(level + 1)

    med = np.median(level)
    spread = np.median(np.abs(level - med)) * 1.4826 or 1e-6   # robust std
    z = (level - med) / spread
    bad = np.abs(z) > NOISE_Z

    segments, start = [], None
    for i, b in enumerate(list(bad) + [False]):
        if b and start is None:
            start = i
        elif not b and start is not None:
            if i - start >= 3:            # at least 300 ms long
                segments.append((start * FRAME_MS / 1000, i * FRAME_MS / 1000))
            start = None
    return segments


# =========================================================
# 5. DIGITAL SILENCE (deleted / muted section)
# =========================================================

def find_digital_silence(x, rate):
    need = rate * SILENCE_MS // 1000
    zero = np.concatenate([[False], x == 0, [False]])
    edges = np.flatnonzero(np.diff(zero.astype(np.int8)))
    runs = edges.reshape(-1, 2)
    return [(s / rate, e / rate) for s, e in runs if e - s >= need]


# =========================================================
# 6. LSB STEGANOGRAPHY
# =========================================================

def lsb_hide(x, message):
    bits = np.unpackbits(np.frombuffer(message.encode() + b"\x00", dtype=np.uint8))
    y = x.copy()
    y[: len(bits)] = (y[: len(bits)] & ~1) | bits
    return y


def lsb_extract(x, max_chars=500):
    raw = np.packbits((x[: max_chars * 8] & 1).astype(np.uint8)).tobytes()
    text = raw.split(b"\x00", 1)[0]
    if len(text) >= 4 and all(32 <= c < 127 for c in text) and b"\x00" in raw:
        return text.decode()
    return None


# =========================================================
# 7. WAVEFORM IMAGE
# =========================================================

def draw_waveform(x, rate, marks, path, width=1000, height=240):
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    mid = height // 2
    cols = np.array_split(x.astype(np.float64), width)
    peak = max(np.abs(x).max(), 1)
    for i, c in enumerate(cols):
        if len(c):
            d.line([(i, mid - c.max() / peak * mid), (i, mid - c.min() / peak * mid)], fill="#1f4e78")
    total = len(x) / rate
    for start, end in marks:
        x1 = int(start / total * width)
        x2 = max(int(end / total * width), x1 + 2)
        d.rectangle([x1, 0, x2, height - 1], outline="red", width=2)
    img.save(path)


# =========================================================
# ANALYSE ONE FILE
# =========================================================

def analyse(path, out_dir):
    with open(path, "rb") as f:
        data = f.read()
    name = os.path.basename(path)
    lines = ["=" * 64, f" AUDIO FORENSIC REPORT: {name}", "=" * 64, f"File size : {len(data)} bytes",
             f"MD5       : {hashlib.md5(data).hexdigest()}",
             f"SHA-256   : {hashlib.sha256(data).hexdigest()}"]
    suspicious, marks = [], []

    findings, chunks = header_checks(path, data)
    suspicious += findings
    lines += [f"Header    : {f}" for f in findings] or ["Header    : consistent"]
    if not chunks:
        return lines + ["Cannot analyse further."], suspicious

    info = read_info(data, chunks)
    lines.append("\n--- Metadata ---")
    lines += [f"{k}: {v}" for k, v in info.items()] or ["(none)"]
    if any(s in info.get("Software", "").lower() for s in EDITING_SOFTWARE):
        suspicious.append(f"Saved by editing software: {info['Software']}")

    with wave.open(path, "rb") as w:
        rate, width, channels = w.getframerate(), w.getsampwidth(), w.getnchannels()
        if width != 2:
            return lines + ["Only 16-bit PCM is supported."], suspicious
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")[::channels]
    lines.append(f"Format    : {rate} Hz, 16-bit, {channels} channel(s), {len(x) / rate:.2f} s")

    lines.append("\n--- Splice detection ---")
    for t in find_jumps(x, rate):
        suspicious.append(f"Sudden sample jump (splice point) at {t:.2f} s")
        lines.append(suspicious[-1])
        marks.append((t, t))
    for s, e in find_noise_changes(x, rate):
        suspicious.append(f"Background noise changes between {s:.1f} s and {e:.1f} s (inserted segment?)")
        lines.append(suspicious[-1])
        marks.append((s, e))
    if not marks:
        lines.append("No splice found")

    lines.append("\n--- Deleted / muted sections ---")
    silences = find_digital_silence(x, rate)
    for s, e in silences:
        suspicious.append(f"Exact digital silence {s:.2f}-{e:.2f} s (section erased?)")
        lines.append(suspicious[-1])
        marks.append((s, e))
    if not silences:
        lines.append("None found")

    lines.append("\n--- LSB steganography ---")
    hidden = lsb_extract(x)
    if hidden:
        suspicious.append("LSB hidden message present")
        lines.append(f'Hidden message found: "{hidden}"')
    else:
        lines.append("No hidden LSB text found")

    wave_png = os.path.join(out_dir, os.path.splitext(name)[0] + "_waveform.png")
    draw_waveform(x, rate, marks, wave_png)
    lines.append(f"\nWaveform image (red = suspicious): {wave_png}")

    lines.append("\n--- VERDICT ---")
    lines += (["SUSPICIOUS:"] + [f"  - {s}" for s in suspicious]) if suspicious else ["No signs of tampering found"]
    return lines, suspicious


# =========================================================
# DEMO: create sample recordings
# =========================================================

RATE = 16000


def recording(seed, seconds, noise):
    """Speech-like signal: changing tones with a syllable envelope + room noise."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * RATE)) / RATE
    pitch = 180 + 40 * np.sin(2 * np.pi * 0.7 * t + seed)
    phase = 2 * np.pi * np.cumsum(pitch) / RATE
    voice = np.sin(phase) + 0.5 * np.sin(2 * phase) + 0.25 * np.sin(3 * phase)
    envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 3 * t) ** 2
    signal = 0.3 * voice * envelope + rng.normal(0, noise, len(t))
    return np.clip(signal * 32767, -32768, 32767).astype(np.int16)


def make_demo(folder):
    os.makedirs(folder, exist_ok=True)
    recorder = {"Artist": "Witness phone", "Created": "2026-10-20", "Software": "Voice Recorder 3.1"}
    original = recording(1, 6, 0.004)

    # 1. Original call recording
    write_wav(os.path.join(folder, "original.wav"), original, RATE, recorder)

    # 2. Spliced: 1.5 s from another recording (noisier room) inserted at 2.0 s
    other = recording(7, 1.5, 0.03)
    spliced = np.concatenate([original[: 2 * RATE], other, original[2 * RATE:]])
    write_wav(os.path.join(folder, "spliced.wav"), spliced, RATE, {**recorder, "Software": "Audacity 3.4"})

    # 3. Muted: 1 s of the conversation erased to silence at 3.0 s
    muted = original.copy()
    muted[3 * RATE: 4 * RATE] = 0
    write_wav(os.path.join(folder, "muted.wav"), muted, RATE, recorder)

    # 4. Secret message hidden in sample LSBs
    write_wav(os.path.join(folder, "stego.wav"), lsb_hide(original, "Transfer 5 lakh on Friday"), RATE, recorder)

    # 5. WAV disguised as MP3
    write_wav(os.path.join(folder, "song.mp3"), original, RATE)

    return sorted(os.path.join(folder, f) for f in os.listdir(folder))


def self_check(results):
    def flags(name):
        return " ".join(results[name])

    assert results["original.wav"] == [], results["original.wav"]
    assert "splice" in flags("spliced.wav") or "noise changes" in flags("spliced.wav")
    assert "Audacity" in flags("spliced.wav")
    assert "digital silence" in flags("muted.wav")
    assert "LSB" in flags("stego.wav")
    assert "MISMATCH" in flags("song.mp3")
    print("\nSelf-check passed: every planted artefact was detected, original is clean.")


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio forensic analysis tool")
    parser.add_argument("files", nargs="*", help="WAV files to analyse")
    parser.add_argument("--demo", action="store_true", help="create and analyse sample recordings")
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
