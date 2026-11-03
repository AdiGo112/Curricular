# =========================================================
# ASSIGNMENT 4
# Three-level Hierarchical JPEG: Encoder and Decoder
# =========================================================
#
# Hierarchical (progressive-resolution) JPEG stores an image
# as a pyramid, so a viewer can show a small version first
# and refine it.
#
#   ENCODER
#   1. Build a 3-level pyramid by down-sampling 2x each time
#        L0 = full size, L1 = 1/2, L2 = 1/4
#   2. Code L2 (smallest) normally:  DCT -> quantize
#   3. Decode L2, up-sample it to the size of L1 = prediction
#      Code only the DIFFERENCE  L1 - prediction
#   4. Do the same for L0 using the decoded L1
#
#   DECODER
#   1. Decode L2
#   2. Up-sample + add decoded difference -> L1
#   3. Up-sample + add decoded difference -> L0 (final image)
#
#   Transform coding : 8x8 2-D DCT
#   Quantization     : standard JPEG luminance table, scaled
#                      by a quality factor (1-100)
#   Entropy coding   : zig-zag + zlib, only to measure size
#
# =========================================================
# HOW TO RUN
# =========================================================
#
#   pip install numpy pillow
#   python hierarchical_jpeg.py                (built-in test image)
#   python hierarchical_jpeg.py photo.jpg 75   (your image, quality)
#
# Output images are written to the "output" folder.
#
# =========================================================

import os
import sys
import zlib

import numpy as np
from PIL import Image

N = 8   # block size

# Standard JPEG luminance quantization table (ITU-T T.81, Annex K)
Q50 = np.array([
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68, 109, 103, 77],
    [24, 35, 55, 64, 81, 104, 113, 92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103, 99],
], dtype=np.float64)

# 8x8 DCT-II matrix: C[u, x] = a(u) * cos((2x+1) u pi / 16)
C = np.array([[np.sqrt((1 if u == 0 else 2) / N) * np.cos((2 * x + 1) * u * np.pi / (2 * N))
               for x in range(N)] for u in range(N)])

# Zig-zag order: low frequencies first, so zeros group together at the end
ZIGZAG = sorted(((u, v) for u in range(N) for v in range(N)),
                key=lambda p: (p[0] + p[1], p[1] if (p[0] + p[1]) % 2 == 0 else p[0]))


def quant_table(quality):
    """Scale the base table like libjpeg: lower quality = bigger steps."""
    quality = min(max(quality, 1), 100)
    scale = 5000 / quality if quality < 50 else 200 - 2 * quality
    return np.clip(np.floor((Q50 * scale + 50) / 100), 1, 255)


# =========================================================
# TRANSFORM CODING + QUANTIZATION
# =========================================================

def to_blocks(img):
    h, w = img.shape
    return img.reshape(h // N, N, w // N, N).swapaxes(1, 2)        # (rows, cols, 8, 8)


def from_blocks(blocks):
    r, c = blocks.shape[:2]
    return blocks.swapaxes(1, 2).reshape(r * N, c * N)


def encode_plane(plane, q):
    """DCT each 8x8 block and quantize -> integer coefficients."""
    coeffs = C @ to_blocks(plane) @ C.T            # 2-D DCT of every block at once
    return np.round(coeffs / q).astype(np.int32)


def decode_plane(quantized, q):
    """De-quantize and inverse DCT."""
    return from_blocks(C.T @ (quantized * q) @ C)


def entropy_size(quantized):
    """Bytes after zig-zag + zlib (stands in for JPEG's Huffman coding)."""
    zz = np.stack([quantized[..., u, v] for u, v in ZIGZAG], axis=-1)
    return len(zlib.compress(zz.astype(np.int16).tobytes(), 9))


# =========================================================
# PYRAMID HELPERS
# =========================================================

def downsample(img):
    """2x2 average -> half size."""
    h, w = img.shape
    return img.reshape(h // 2, 2, w // 2, 2).mean(axis=(1, 3))


def upsample(img):
    """Bilinear up-sampling to double size (used as the prediction)."""
    h, w = img.shape
    return np.asarray(Image.fromarray(img.astype(np.float32), "F").resize((w * 2, h * 2), Image.BILINEAR),
                      dtype=np.float64)


# =========================================================
# ENCODER
# =========================================================

def encode(image, quality=75, diff_quality=None):
    """Return the bit-stream (dict) holding the 3 coded levels."""
    q = quant_table(quality)
    qd = quant_table(diff_quality or quality)

    L0 = image.astype(np.float64)
    L1 = downsample(L0)
    L2 = downsample(L1)

    stream = {"shape": L0.shape, "quality": quality, "diff_quality": diff_quality or quality}

    # Level 2: normal (non-differential) JPEG of the smallest image, level shift by 128
    stream["L2"] = encode_plane(L2 - 128, q)
    rec2 = decode_plane(stream["L2"], q) + 128

    # Level 1: code only the difference from the up-sampled level 2
    stream["D1"] = encode_plane(L1 - upsample(rec2), qd)
    rec1 = upsample(rec2) + decode_plane(stream["D1"], qd)

    # Level 0: difference from the up-sampled level 1
    stream["D0"] = encode_plane(L0 - upsample(rec1), qd)
    return stream, (L2, L1, L0)


# =========================================================
# DECODER (uses only the bit-stream)
# =========================================================

def decode(stream):
    q = quant_table(stream["quality"])
    qd = quant_table(stream["diff_quality"])

    rec2 = decode_plane(stream["L2"], q) + 128
    rec1 = upsample(rec2) + decode_plane(stream["D1"], qd)
    rec0 = upsample(rec1) + decode_plane(stream["D0"], qd)
    return [np.clip(np.round(r), 0, 255).astype(np.uint8) for r in (rec2, rec1, rec0)]


# =========================================================
# QUALITY MEASURE
# =========================================================

def psnr(a, b):
    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    return float("inf") if mse == 0 else 10 * np.log10(255 ** 2 / mse)


def test_image(size=256):
    """Built-in test picture: gradients, circles, stripes and text-like detail."""
    y, x = np.mgrid[0:size, 0:size]
    img = 60 + 120 * x / size
    img += 50 * ((x - 90) ** 2 + (y - 90) ** 2 < 50 ** 2)
    img -= 40 * ((x - 180) ** 2 + (y - 170) ** 2 < 40 ** 2)
    img += 30 * (np.sin(x / 3) > 0) * (y > 200)
    img += 25 * ((x // 16 + y // 16) % 2) * (x < 64) * (y > 150)
    return np.clip(img, 0, 255).astype(np.uint8)


def load_image(path):
    img = np.asarray(Image.open(path).convert("L"))
    h, w = img.shape
    m = 4 * N                                          # each level must still be whole 8x8 blocks
    return img[: h - h % m, : w - w % m]


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "output")
    os.makedirs(out, exist_ok=True)

    image = load_image(sys.argv[1]) if len(sys.argv) > 1 else test_image()
    quality = int(sys.argv[2]) if len(sys.argv) > 2 else 75

    stream, originals = encode(image, quality)

    # Save the bit-stream, then decode it from the file (true encoder/decoder separation)
    stream_file = os.path.join(out, "image_hjpeg.npz")
    with open(stream_file, "wb") as f:
        np.savez_compressed(f, **stream)
    with open(stream_file, "rb") as f:
        levels = decode(dict(np.load(f, allow_pickle=False)))

    print("=" * 66)
    print(f" Three-level Hierarchical JPEG   (quality {quality})")
    print("=" * 66)
    print(f"{'Level':8}{'Size':12}{'Coded as':22}{'Bytes':>8}{'PSNR (dB)':>12}")
    print("-" * 66)

    names = ["L2 1/4", "L1 1/2", "L0 full"]
    keys = ["L2", "D1", "D0"]
    kinds = ["DCT of image", "DCT of difference", "DCT of difference"]
    total = 0
    for name, key, kind, orig, rec in zip(names, keys, kinds, originals, levels):
        size = entropy_size(stream[key])
        total += size
        h, w = rec.shape
        p = psnr(np.clip(np.round(orig), 0, 255), rec)
        print(f"{name:8}{f'{w}x{h}':12}{kind:22}{size:8}{p:12.2f}")
        Image.fromarray(rec).save(os.path.join(out, f"decoded_{name.split()[0]}.png"))

    raw = image.size
    print("-" * 66)
    print(f"Original: {raw} bytes   Hierarchical stream: {total} bytes   "
          f"Compression ratio: {raw / total:.1f}:1")

    Image.fromarray(image).save(os.path.join(out, "original.png"))
    diff = np.abs(image.astype(int) - levels[2].astype(int))
    Image.fromarray(np.clip(diff * 8, 0, 255).astype(np.uint8)).save(os.path.join(out, "error_x8.png"))
    print(f"Images saved in: {out}")

    # Quality vs size table
    print("\nEffect of quantization (quality factor):")
    print(f"{'Quality':>8}{'Bytes':>9}{'Ratio':>8}{'PSNR':>9}")
    for qf in (10, 30, 50, 75, 90):
        s, _ = encode(image, qf)
        size = sum(entropy_size(s[k]) for k in keys)
        print(f"{qf:8}{size:9}{raw / size:8.1f}{psnr(image, decode(s)[2]):9.2f}")

    # ---------- self-check ----------
    # 1. DCT is exactly invertible without quantization
    block = np.random.default_rng(0).uniform(-128, 127, (N, N))
    assert np.allclose(C.T @ (C @ block @ C.T) @ C, block)
    # 2. Full-size result is good quality and better quality means bigger file
    assert psnr(image, levels[2]) > 30
    s90, _ = encode(image, 90)
    s10, _ = encode(image, 10)
    assert sum(entropy_size(s90[k]) for k in keys) > sum(entropy_size(s10[k]) for k in keys)
    print("\nSelf-check passed.")
