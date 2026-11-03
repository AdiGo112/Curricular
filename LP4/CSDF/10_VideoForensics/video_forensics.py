# =========================================================
# MINI PROJECT 10
# Tool for Digital Forensics of Video
# =========================================================
#
# Checks performed on a video (evidence):
#
#   1. Hashing (MD5, SHA-256)           -> integrity
#   2. File signature                   -> renamed / disguised file
#   3. Metadata                         -> resolution, FPS, codec,
#                                          duration, encoder /
#                                          creation time (ffprobe)
#   4. Frame deletion detection         -> sudden jump in motion
#                                          between two frames
#   5. Frame duplication / freeze       -> identical frames repeated
#                                          to hide an event
#   6. Evidence frames                  -> frames before/after each
#                                          suspicious point saved
#                                          as images
#
# =========================================================
# HOW TO RUN
# =========================================================
#
#   pip install opencv-python numpy
#   (optional) install ffmpeg for encoder / creation-time metadata
#
#   python video_forensics.py --demo         (creates sample CCTV
#                                             clips and analyses them)
#   python video_forensics.py cctv.mp4       (your own file)
#
# =========================================================

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np

SIGNATURES = [
    (4, b"ftyp", "MP4/MOV", [".mp4", ".mov", ".m4v", ".3gp"]),
    (0, b"RIFF", "AVI", [".avi"]),
    (0, b"\x1a\x45\xdf\xa3", "MKV/WebM", [".mkv", ".webm"]),
]

EDITING_SOFTWARE = ["premiere", "after effects", "davinci", "filmora", "capcut", "kinemaster", "imovie", "vegas"]

PIXEL_CHANGE = 15      # a pixel "changed" if its brightness moved by more than this
JUMP_FACTOR = 4.0      # motion > 4x the typical motion = deleted frames
FREEZE_DIFF = 0.05     # less than 0.05 % pixels changed = duplicate frame
FREEZE_MIN = 10        # at least this many duplicate frames in a row = freeze


# =========================================================
# 1-3. HASH, SIGNATURE, METADATA
# =========================================================

def hashes(path):
    md5, sha = hashlib.md5(), hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):   # large files: read in 1 MB parts
            md5.update(chunk)
            sha.update(chunk)
    return md5.hexdigest(), sha.hexdigest()


def check_signature(path):
    with open(path, "rb") as f:
        head = f.read(16)
    ext = os.path.splitext(path)[1].lower()
    for offset, magic, kind, exts in SIGNATURES:
        if head[offset:offset + len(magic)] == magic:
            if ext in exts:
                return kind, None
            return kind, f"MISMATCH: extension '{ext}' but content is {kind}"
    return "Unknown", "Unknown video signature"


def ffprobe_tags(path):
    """Container tags such as encoder and creation_time (needs ffmpeg installed)."""
    if not shutil.which("ffprobe"):
        return None
    out = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
                         capture_output=True, text=True)
    try:
        return json.loads(out.stdout).get("format", {}).get("tags", {})
    except json.JSONDecodeError:
        return None


# =========================================================
# 4-5. FRAME ANALYSIS
# =========================================================

def frame_differences(path):
    """Percentage of pixels that changed between every pair of neighbouring frames."""
    cap = cv2.VideoCapture(path)
    diffs, prev, frames = [], None, 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(cv2.resize(frame, (320, 180)), cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None:
            diffs.append(100 * float(np.mean(np.abs(gray - prev) > PIXEL_CHANGE)))
        prev = gray
        frames += 1
    cap.release()
    return np.array(diffs), frames


def find_jumps(diffs):
    moving = diffs[diffs > FREEZE_DIFF]
    if len(moving) < 5:
        return []
    typical = np.median(moving)
    return [int(i) + 1 for i in np.where(diffs > JUMP_FACTOR * typical)[0]]   # frame index after the jump


def find_freezes(diffs):
    still = np.concatenate([[False], diffs < FREEZE_DIFF, [False]])
    edges = np.flatnonzero(np.diff(still.astype(np.int8))).reshape(-1, 2)
    return [(s, e) for s, e in edges if e - s >= FREEZE_MIN]   # frames s .. e are identical


def save_frames(path, indexes, out_dir, prefix):
    cap = cv2.VideoCapture(path)
    saved = []
    for i in indexes:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, frame = cap.read()
        if ok:
            name = os.path.join(out_dir, f"{prefix}_frame{i}.png")
            cv2.imwrite(name, frame)
            saved.append(name)
    cap.release()
    return saved


# =========================================================
# ANALYSE ONE FILE
# =========================================================

def analyse(path, out_dir):
    name = os.path.basename(path)
    prefix = os.path.splitext(name)[0]
    md5, sha = hashes(path)
    lines = ["=" * 64, f" VIDEO FORENSIC REPORT: {name}", "=" * 64,
             f"File size : {os.path.getsize(path)} bytes", f"MD5       : {md5}", f"SHA-256   : {sha}"]
    suspicious = []

    kind, problem = check_signature(path)
    lines.append(f"Signature : {kind}" + (f" ({problem})" if problem else " (matches extension)"))
    if problem:
        suspicious.append(problem)

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return lines + ["Cannot open video."], suspicious
    fps = cap.get(cv2.CAP_PROP_FPS)
    declared = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC)).to_bytes(4, "little").decode("latin-1")
    cap.release()

    lines.append("\n--- Metadata ---")
    lines.append(f"Resolution: {w}x{h}   FPS: {fps:.2f}   Codec: {fourcc}")
    tags = ffprobe_tags(path)
    if tags is None:
        lines.append("Container tags: (install ffmpeg to read encoder / creation time)")
    else:
        lines += [f"{k}: {v}" for k, v in tags.items()] or ["Container tags: none"]
        encoder = " ".join(str(v) for v in tags.values()).lower()
        for s in EDITING_SOFTWARE:
            if s in encoder:
                suspicious.append(f"Video was exported by editing software ({s})")

    diffs, frames = frame_differences(path)
    lines.append(f"Frames    : {frames} decoded (header says {declared}), duration {frames / fps:.2f} s")

    lines.append("\n--- Frame deletion (motion jumps) ---")
    jumps = find_jumps(diffs)
    for i in jumps:
        msg = f"Abrupt jump at frame {i} ({i / fps:.2f} s): frames deleted or clip cut"
        suspicious.append(msg)
        lines.append(msg)
        lines += [f"  evidence: {p}" for p in save_frames(path, [i - 1, i], out_dir, prefix)]
    if not jumps:
        lines.append("Motion is continuous")

    lines.append("\n--- Frame duplication / freeze ---")
    freezes = find_freezes(diffs)
    for s, e in freezes:
        msg = f"Frames {s}-{e} identical ({(e - s + 1) / fps:.2f} s freeze): event may be hidden"
        suspicious.append(msg)
        lines.append(msg)
        lines += [f"  evidence: {p}" for p in save_frames(path, [s, e], out_dir, prefix)]
    if not freezes:
        lines.append("No frozen / duplicated sequence")

    lines.append("\n--- VERDICT ---")
    lines += (["SUSPICIOUS:"] + [f"  - {s}" for s in suspicious]) if suspicious else ["No signs of tampering found"]
    return lines, suspicious


# =========================================================
# DEMO: synthetic CCTV clips
# =========================================================

FPS, W, H = 25, 640, 360


def cctv_frames(count=150):
    """A person (circle) walks across a room; the camera clock ticks every frame."""
    frames = []
    for i in range(count):
        img = np.full((H, W, 3), 60, np.uint8)
        cv2.rectangle(img, (0, 260), (W, H), (90, 90, 90), -1)              # floor
        cv2.rectangle(img, (480, 80), (560, 260), (40, 70, 120), -1)        # door
        x = 40 + i * 4
        cv2.circle(img, (x, 220), 30, (200, 180, 160), -1)                  # person
        cv2.putText(img, f"CAM-02  21:14:{i // FPS:02d}.{i % FPS:02d}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        frames.append(img)
    return frames


def write_video(path, frames):
    out = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
    for f in frames:
        out.write(f)
    out.release()


def make_demo(folder):
    os.makedirs(folder, exist_ok=True)
    frames = cctv_frames()

    write_video(os.path.join(folder, "original.mp4"), frames)
    # 40 frames (1.6 s) cut out: the person "teleports"
    write_video(os.path.join(folder, "deleted.mp4"), frames[:60] + frames[100:])
    # frame 60 repeated for 40 frames (1.6 s) to hide what happened
    write_video(os.path.join(folder, "frozen.mp4"), frames[:60] + [frames[60]] * 40 + frames[100:])
    # MP4 renamed to look like a document
    shutil.copy(os.path.join(folder, "original.mp4"), os.path.join(folder, "minutes.pdf"))

    return sorted(os.path.join(folder, f) for f in os.listdir(folder))


def self_check(results):
    def flags(name):
        return " ".join(results[name])

    assert results["original.mp4"] == [], results["original.mp4"]
    assert "Abrupt jump at frame 60" in flags("deleted.mp4")
    assert "freeze" in flags("frozen.mp4")
    assert "MISMATCH" in flags("minutes.pdf")
    print("\nSelf-check passed: every planted artefact was detected, original is clean.")


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video forensic analysis tool")
    parser.add_argument("files", nargs="*", help="video files to analyse")
    parser.add_argument("--demo", action="store_true", help="create and analyse sample CCTV clips")
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
