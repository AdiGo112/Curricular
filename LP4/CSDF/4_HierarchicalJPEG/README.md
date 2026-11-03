# Assignment 4: Three-level Hierarchical JPEG Encoder and Decoder

```bash
pip install numpy pillow
python hierarchical_jpeg.py                 # built-in 256x256 test image, quality 75
python hierarchical_jpeg.py photo.jpg 50    # your own image (converted to grayscale)
```

## How It Works

```
ENCODER                                         DECODER
L0 (full) ──2x2 avg──> L1 (1/2) ──2x2 avg──> L2 (1/4)
                                               │
                     DCT + Quantize  <─────────┘  ──> stream "L2" ──> IDCT ──> L2'
L1 - upsample(L2') ─> DCT + Quantize ────────────> stream "D1" ──> IDCT + upsample(L2') ──> L1'
L0 - upsample(L1') ─> DCT + Quantize ────────────> stream "D0" ──> IDCT + upsample(L1') ──> L0'  (final)
```

| Step | Concept | Code |
| --- | --- | --- |
| Transform coding | 8×8 2-D DCT: `F = C · B · Cᵀ` (energy moves into a few low-frequency coefficients) | `encode_plane` |
| Quantization | Divide by the JPEG luminance table scaled by quality, then round. This is the only lossy step | `quant_table`, `encode_plane` |
| Hierarchical coding | Smallest level coded normally, larger levels code only the **difference** from the up-sampled lower level | `encode`, `decode` |
| Entropy coding | Zig-zag scan + zlib, used to measure the compressed size | `entropy_size` |

The encoder uses the **decoded** (not original) lower level for prediction, so encoder and decoder stay in step and errors do not add up across levels. The bit-stream is saved to `output/image_hjpeg.npz` and decoded back from that file.

## Results (built-in image, quality 75)

| Level | Size | Coded as | Bytes | PSNR |
| --- | --- | --- | --- | --- |
| L2 | 64×64 | DCT of image | 783 | 39.5 dB |
| L1 | 128×128 | DCT of difference | 1,507 | 42.4 dB |
| L0 | 256×256 | DCT of difference | 4,077 | 42.8 dB |

Total: 6,367 bytes instead of 65,536 (**10.3 : 1**). Lower quality gives a smaller stream but lower PSNR (quality 10 gives 43 : 1 at 33.8 dB).

Output images: `output/decoded_L2.png`, `decoded_L1.png`, `decoded_L0.png`, `original.png`, `error_x8.png` (error ×8 so it is visible).
