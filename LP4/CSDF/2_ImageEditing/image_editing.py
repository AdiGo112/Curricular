# =========================================================
# ASSIGNMENT 2
# JPEG Image demonstrating features of an Image Editing tool
# =========================================================
#
# The same operations found in GIMP / Photoshop are applied
# with Pillow (Python Imaging Library), and every result is
# placed on one labelled sheet saved as a JPEG:
#
#   Geometry   : crop, resize, rotate, flip
#   Tone       : brightness, contrast, grayscale, sepia,
#                invert, posterize, auto-contrast
#   Colour     : saturation boost, colour balance (warm)
#   Filters    : blur, sharpen, edge detect, emboss
#   Layers     : text overlay, transparent watermark
#                (alpha blending), vignette, border
#
# Every operation is also saved as its own JPEG in output/.
#
# =========================================================
# HOW TO RUN
# =========================================================
#
#   pip install pillow numpy
#   python image_editing.py              (built-in sample photo)
#   python image_editing.py myphoto.jpg  (your own photo)
#
# GIMP equivalents are listed in README.md.
#
# =========================================================

import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

TILE = (320, 213)   # size of each thumbnail on the sheet


def sample_photo(w=960, h=640):
    """Draw a landscape (sky, sun, mountains, lake, trees) to edit."""
    y, x = np.mgrid[0:h, 0:w]
    img = np.zeros((h, w, 3))
    t = y / h
    img[..., 0] = 90 + 120 * t
    img[..., 1] = 150 + 70 * t
    img[..., 2] = 235 - 20 * t                              # sky gradient
    sun = (x - 720) ** 2 + (y - 150) ** 2 < 70 ** 2
    img[sun] = [255, 220, 120]
    ridge = 330 + 60 * np.sin(x / 90) + 30 * np.sin(x / 37)
    img[y > ridge] = [70, 95, 120]                          # far mountains
    hill = 400 + 40 * np.sin(x / 140 + 1)
    img[y > hill] = [60, 130, 70]                           # hills
    lake = y > 520
    img[lake] = [40, 110, 170] + 15 * np.sin(x[lake] / 7 + y[lake])[:, None]
    for tx in (120, 200, 860):                              # pine trees
        trunk = (abs(x - tx) < 6) & (y > 430) & (y < 520)
        crown = (y > 320) & (y < 470) & (abs(x - tx) < (y - 320) * 0.35)
        img[trunk] = [90, 60, 30]
        img[crown] = [30, 90, 40]
    noise = np.random.default_rng(1).normal(0, 6, img.shape)  # photo grain
    return Image.fromarray(np.clip(img + noise, 0, 255).astype(np.uint8))


def font(size):
    for name in ("arialbd.ttf", "DejaVuSans-Bold.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


# =========================================================
# EDITING OPERATIONS
# =========================================================

def sepia(img):
    g = np.asarray(ImageOps.grayscale(img), dtype=np.float64)
    return Image.fromarray(np.clip(np.stack([g * 1.07 + 20, g * 0.95 + 5, g * 0.75], 2), 0, 255).astype(np.uint8))


def warm_balance(img):
    r, g, b = img.split()
    return Image.merge("RGB", (r.point(lambda v: min(255, v + 25)), g, b.point(lambda v: max(0, v - 25))))


def text_overlay(img):
    out = img.copy()
    d = ImageDraw.Draw(out)
    d.text((30, img.height - 90), "Sunrise Valley", font=font(56), fill="white",
           stroke_width=3, stroke_fill="black")
    return out


def watermark(img):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((img.width // 2, img.height // 2), "© SAMPLE", font=font(110), fill=(255, 255, 255, 90),
           anchor="mm")
    return Image.alpha_composite(img.convert("RGBA"), layer.rotate(25)).convert("RGB")


def vignette(img):
    w, h = img.size
    y, x = np.mgrid[0:h, 0:w]
    r = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2)
    mask = np.clip(1.15 - 0.6 * r ** 2, 0, 1)[..., None]
    return Image.fromarray((np.asarray(img) * mask).astype(np.uint8))


OPERATIONS = [
    ("Original", lambda im: im),
    ("Crop", lambda im: im.crop((480, 60, 960, 380))),
    ("Resize 25%", lambda im: im.resize((im.width // 4, im.height // 4), Image.LANCZOS)),
    ("Rotate 15°", lambda im: im.rotate(15, expand=True, fillcolor="white")),
    ("Flip horizontal", ImageOps.mirror),
    ("Brightness +40%", lambda im: ImageEnhance.Brightness(im).enhance(1.4)),
    ("Contrast +80%", lambda im: ImageEnhance.Contrast(im).enhance(1.8)),
    ("Saturation x2", lambda im: ImageEnhance.Color(im).enhance(2.0)),
    ("Grayscale", lambda im: ImageOps.grayscale(im).convert("RGB")),
    ("Sepia", sepia),
    ("Invert (negative)", ImageOps.invert),
    ("Posterize 3-bit", lambda im: ImageOps.posterize(im, 3)),
    ("Auto contrast", lambda im: ImageOps.autocontrast(im, cutoff=2)),
    ("Warm balance", warm_balance),
    ("Gaussian blur", lambda im: im.filter(ImageFilter.GaussianBlur(6))),
    ("Sharpen", lambda im: im.filter(ImageFilter.UnsharpMask(4, 200, 2))),
    ("Edge detect", lambda im: im.filter(ImageFilter.FIND_EDGES)),
    ("Emboss", lambda im: im.filter(ImageFilter.EMBOSS)),
    ("Text overlay", text_overlay),
    ("Watermark (alpha)", watermark),
    ("Vignette", vignette),
    ("Border / frame", lambda im: ImageOps.expand(im, border=30, fill=(245, 240, 225))),
]


def contact_sheet(results, cols=4):
    rows = -(-len(results) // cols)
    label_h, pad = 34, 14
    W = cols * (TILE[0] + pad) + pad
    H = 90 + rows * (TILE[1] + label_h + pad) + pad
    sheet = Image.new("RGB", (W, H), (30, 33, 40))
    d = ImageDraw.Draw(sheet)
    d.text((W // 2, 45), "Image Editing Tool - Feature Demonstration", font=font(38), fill="white", anchor="mm")
    for i, (name, img) in enumerate(results):
        r, c = divmod(i, cols)
        x = pad + c * (TILE[0] + pad)
        y = 90 + r * (TILE[1] + label_h + pad)
        thumb = ImageOps.contain(img, TILE)
        sheet.paste(thumb, (x + (TILE[0] - thumb.width) // 2, y + (TILE[1] - thumb.height) // 2))
        d.text((x + TILE[0] // 2, y + TILE[1] + label_h // 2), f"{i + 1}. {name}", font=font(20),
               fill=(230, 230, 230), anchor="mm")
    return sheet


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "output")
    os.makedirs(out, exist_ok=True)

    photo = Image.open(sys.argv[1]).convert("RGB") if len(sys.argv) > 1 else sample_photo()

    results = []
    for i, (name, op) in enumerate(OPERATIONS, 1):
        edited = op(photo).convert("RGB")
        results.append((name, edited))
        fname = f"{i:02d}_{name.split()[0].lower()}.jpg"
        edited.save(os.path.join(out, fname), "JPEG", quality=90)
        print(f"{i:2}. {name:20} -> output/{fname}  {edited.size[0]}x{edited.size[1]}")

    sheet_path = os.path.join(here, "image_editing_features.jpg")
    contact_sheet(results).save(sheet_path, "JPEG", quality=92, optimize=True, progressive=True)
    print(f"\nFeature sheet saved: {sheet_path}")
