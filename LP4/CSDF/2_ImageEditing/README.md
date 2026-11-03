# Assignment 2: JPEG Image Demonstrating Image Editing Features

`image_editing.py` applies 22 editing operations to a photo and saves:
- `image_editing_features.jpg`: one labelled JPEG sheet showing every feature (the deliverable)
- `output/01_original.jpg … output/22_border.jpg`: each edit as its own JPEG

```bash
pip install pillow numpy
python image_editing.py              # built-in landscape photo
python image_editing.py myphoto.jpg  # your own photo
```

## Features and their GIMP Equivalents

| # | Feature | Category | GIMP menu |
| --- | --- | --- | --- |
| 1 | Original | — | File → Open |
| 2 | Crop | Geometry | Tools → Transform Tools → Crop |
| 3 | Resize / scale | Geometry | Image → Scale Image |
| 4 | Rotate | Geometry | Layer → Transform → Arbitrary Rotation |
| 5 | Flip | Geometry | Image → Transform → Flip Horizontally |
| 6 | Brightness | Tone | Colors → Brightness-Contrast |
| 7 | Contrast | Tone | Colors → Brightness-Contrast |
| 8 | Saturation | Colour | Colors → Hue-Saturation |
| 9 | Grayscale | Colour | Colors → Desaturate |
| 10 | Sepia | Colour | Filters → Decor → Old Photo / Colors → Map |
| 11 | Invert | Colour | Colors → Invert |
| 12 | Posterize | Colour | Colors → Posterize |
| 13 | Auto contrast | Tone | Colors → Auto → Stretch Contrast |
| 14 | Colour balance (warm) | Colour | Colors → Color Balance |
| 15 | Gaussian blur | Filter | Filters → Blur → Gaussian Blur |
| 16 | Sharpen | Filter | Filters → Enhance → Unsharp Mask |
| 17 | Edge detect | Filter | Filters → Edge-Detect → Edge |
| 18 | Emboss | Filter | Filters → Distorts → Emboss |
| 19 | Text overlay | Layers | Tools → Text |
| 20 | Watermark (alpha) | Layers | New transparent layer + text, lower Opacity |
| 21 | Vignette | Effect | Filters → Light and Shadow → Vignette |
| 22 | Border / frame | Effect | Filters → Decor → Add Border |

## Why JPEG?
JPEG uses lossy compression (DCT and quantization, the same steps as in Assignment 4), so photos become much smaller. The sheet is saved at quality 92 with the `progressive` option, so it loads blurry-to-sharp in a browser.
