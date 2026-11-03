# =========================================================
# ASSIGNMENT 2
# Generate and Verify a CAPTCHA Image
# =========================================================
#
# CAPTCHA = Completely Automated Public Turing test to tell
# Computers and Humans Apart.
#
# GENERATION (hard for OCR bots, easy for humans)
#   - random 6 characters, without look-alikes (0/O, 1/l/I)
#   - each character in a random font size, colour and angle
#   - wavy distortion of the whole image
#   - noise: random lines, arcs and dots
#
# VERIFICATION (secure on the server side)
#   - the answer is NEVER stored in plain text: only an HMAC
#     (keyed hash) of it, so leaked data does not reveal it
#   - case-insensitive, spaces ignored
#   - expires after 2 minutes
#   - maximum 3 attempts, then a new CAPTCHA is needed
#   - one-time use: a solved CAPTCHA cannot be replayed
#
# =========================================================
# HOW TO USE
# =========================================================
#
#   pip install pillow numpy
#   python captcha.py            interactive: image opens, type the text
#   python captcha.py --test     automatic self-test of all rules
#
# =========================================================

import argparse
import hashlib
import hmac
import math
import os
import secrets
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZabdefghjkmnpqrstuvwxyz23456789"   # no 0 O 1 l I c o
LENGTH = 6
EXPIRY_SECONDS = 120
MAX_ATTEMPTS = 3
SERVER_KEY = secrets.token_bytes(32)          # secret known only to the server

FONTS = ["arialbd.ttf", "georgiab.ttf", "verdanab.ttf", "courbd.ttf",
         "DejaVuSans-Bold.ttf", "DejaVuSerif-Bold.ttf"]


def load_font(size):
    for name in secrets.SystemRandom().sample(FONTS, len(FONTS)):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


# =========================================================
# GENERATION
# =========================================================

def random_text():
    return "".join(secrets.choice(CHARS) for _ in range(LENGTH))


def draw_captcha(text, width=280, height=90):
    rnd = secrets.SystemRandom()
    img = Image.new("RGB", (width, height), (rnd.randint(225, 250), rnd.randint(225, 250), rnd.randint(225, 250)))

    # background noise dots
    d = ImageDraw.Draw(img)
    for _ in range(600):
        d.point((rnd.randrange(width), rnd.randrange(height)),
                fill=(rnd.randint(120, 220), rnd.randint(120, 220), rnd.randint(120, 220)))

    # each character on its own rotated tile
    x = 12
    for ch in text:
        font = load_font(rnd.randint(34, 46))
        tile = Image.new("RGBA", (60, 70), (0, 0, 0, 0))
        color = (rnd.randint(10, 120), rnd.randint(10, 120), rnd.randint(10, 120), 255)
        ImageDraw.Draw(tile).text((30, 35), ch, font=font, fill=color, anchor="mm")
        tile = tile.rotate(rnd.uniform(-30, 30), resample=Image.BICUBIC, expand=False)
        img.paste(tile, (x, rnd.randint(2, 18)), tile)
        x += rnd.randint(36, 42)

    # wave distortion: shift every column up/down along a sine wave
    arr = np.array(img)
    amp, period, phase = rnd.uniform(3, 6), rnd.uniform(40, 80), rnd.uniform(0, 2 * math.pi)
    for col in range(width):
        arr[:, col] = np.roll(arr[:, col], int(amp * math.sin(2 * math.pi * col / period + phase)), axis=0)
    img = Image.fromarray(arr)

    # interference lines and arcs over the text
    d = ImageDraw.Draw(img)
    for _ in range(4):
        d.line([(rnd.randrange(width // 3), rnd.randrange(height)),
                (rnd.randrange(2 * width // 3, width), rnd.randrange(height))],
               fill=(rnd.randint(40, 140), rnd.randint(40, 140), rnd.randint(40, 140)), width=2)
    for _ in range(2):
        x0, y0 = rnd.randrange(-40, width // 2), rnd.randrange(-20, height // 2)
        d.arc([x0, y0, x0 + rnd.randint(120, 220), y0 + rnd.randint(60, 120)], 0, rnd.randint(120, 300),
              fill=(rnd.randint(40, 140), 60, 90), width=2)

    return img.filter(ImageFilter.SMOOTH)


# =========================================================
# VERIFICATION (server side)
# =========================================================

def normalise(text):
    return "".join(text.split()).lower()


def answer_hash(captcha_id, text):
    # captcha_id is mixed in so the same text gives a different hash every time
    return hmac.new(SERVER_KEY, f"{captcha_id}:{normalise(text)}".encode(), hashlib.sha256).hexdigest()


class CaptchaStore:
    """What a web server would keep in its session / database."""

    def __init__(self):
        self.pending = {}     # id -> {"hash", "created", "attempts"}

    def create(self, now=None):
        captcha_id = secrets.token_hex(8)
        text = random_text()
        self.pending[captcha_id] = {"hash": answer_hash(captcha_id, text),
                                    "created": now or time.time(), "attempts": 0}
        return captcha_id, text, draw_captcha(text)

    def verify(self, captcha_id, user_input, now=None):
        entry = self.pending.get(captcha_id)
        if entry is None:
            return False, "Unknown or already used CAPTCHA - request a new one"
        if (now or time.time()) - entry["created"] > EXPIRY_SECONDS:
            del self.pending[captcha_id]
            return False, "CAPTCHA expired - request a new one"
        entry["attempts"] += 1
        if hmac.compare_digest(entry["hash"], answer_hash(captcha_id, user_input)):
            del self.pending[captcha_id]                       # one-time use
            return True, "Correct - you are human"
        if entry["attempts"] >= MAX_ATTEMPTS:
            del self.pending[captcha_id]
            return False, "Too many wrong attempts - request a new one"
        return False, f"Wrong answer ({MAX_ATTEMPTS - entry['attempts']} attempt(s) left)"


# =========================================================
# SELF-TEST
# =========================================================

def self_test(out_dir):
    store = CaptchaStore()

    cid, text, img = store.create()
    img.save(os.path.join(out_dir, "captcha_sample.png"))
    assert text not in str(store.pending), "answer must not be stored in plain text"
    ok, msg = store.verify(cid, "  " + text.swapcase() + " ")
    print(f"1. Correct answer (different case, extra spaces): {ok}  {msg}")
    assert ok
    ok, msg = store.verify(cid, text)
    print(f"2. Replay the same solved CAPTCHA             : {ok}  {msg}")
    assert not ok

    cid, text, _ = store.create()
    results = [store.verify(cid, "wrong")[1] for _ in range(MAX_ATTEMPTS)]
    ok, msg = store.verify(cid, text)
    print(f"3. Correct answer after {MAX_ATTEMPTS} wrong tries        : {ok}  {msg}")
    print(f"   messages: {results}")
    assert not ok

    cid, text, _ = store.create(now=time.time() - EXPIRY_SECONDS - 1)
    ok, msg = store.verify(cid, text)
    print(f"4. Correct answer after expiry                : {ok}  {msg}")
    assert not ok

    texts = [random_text() for _ in range(2000)]
    assert len(set(texts)) == len(texts), "texts should not repeat"
    assert not any(c in "".join(texts) for c in "0O1lI"), "look-alike characters must be excluded"
    # answers are case-insensitive, so 'A' and 'a' count as one symbol
    alphabet = len(set(normalise(CHARS)))
    print(f"5. 2000 random texts: all unique, no look-alike characters "
          f"({alphabet}^{LENGTH} = {alphabet ** LENGTH:,} possible answers)")

    sheet = Image.new("RGB", (280 * 3, 90 * 3), "white")
    for i in range(9):
        sheet.paste(draw_captcha(random_text()), ((i % 3) * 280, (i // 3) * 90))
    sheet.save(os.path.join(out_dir, "captcha_examples.png"))
    print(f"\nSample images saved in {out_dir}")
    print("Self-test passed.")


# =========================================================
# INTERACTIVE
# =========================================================

def open_image(path):
    try:
        if sys.platform == "win32":
            os.startfile(path)
        else:
            Image.open(path).show()
    except OSError:
        pass
    print(f"(If no window opened, open {path} yourself.)")


def interactive(out_dir):
    store = CaptchaStore()
    while True:
        cid, _, img = store.create()
        path = os.path.join(out_dir, "captcha.png")
        img.save(path)
        open_image(path)
        while cid in store.pending:
            answer = input("Type the characters you see (or 'new' / 'quit'): ")
            if answer.strip().lower() == "quit":
                return
            if answer.strip().lower() == "new":
                del store.pending[cid]
                break
            ok, msg = store.verify(cid, answer)
            print(msg)
            if ok:
                return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CAPTCHA generator and verifier")
    parser.add_argument("--test", action="store_true", help="run the automatic self-test")
    args = parser.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    self_test(here) if args.test else interactive(here)
