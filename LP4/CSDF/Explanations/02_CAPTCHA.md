# Assignment 2: Generate and Verify a CAPTCHA Image

## Aim

Implement a program to generate and verify a CAPTCHA image.

## Theory and Fundamentals

### What is a CAPTCHA?
**CAPTCHA** = *Completely Automated Public Turing test to tell Computers and Humans Apart*. It is a challenge that is easy for a human but hard for a program (a bot). Websites use it on login, sign-up and payment forms to stop automated attacks.

### Why it is needed
- **Brute-force / credential stuffing:** bots try thousands of passwords.
- **Spam and fake accounts:** bots fill forms.
- **Scraping and ticket hoarding.**

### Types
| Type | Example |
| --- | --- |
| Text / image distortion | This assignment |
| Image selection | "Select all traffic lights" (reCAPTCHA v2) |
| Audio CAPTCHA | For visually impaired users |
| Behaviour based / invisible | reCAPTCHA v3, hCaptcha, Cloudflare Turnstile score mouse and device behaviour |
| Math / puzzle | "What is 7 + 3?" |

### How a text CAPTCHA fights OCR bots
OCR (Optical Character Recognition) reads clean text well. To confuse it we add: random font sizes, colours and rotation per character, a wavy distortion of the whole image, and noise (dots, lines, arcs). Look-alike characters (0/O, 1/l/I) are removed so humans are not frustrated.

### Secure verification concepts
- **Server-side check:** the answer must never be trusted from the browser or placed in the page.
- **Hash:** a one-way function (SHA-256). **HMAC** = *Hash-based Message Authentication Code*: a hash computed with a **secret key**. Without the key an attacker who steals the database cannot recompute or guess valid hashes offline.
- **Salting / unique ID:** mixing a random ID into the hash means the same text gives a different value every time.
- **Replay attack:** the attacker re-submits a previously valid answer. Defence: **one-time use** (delete after success).
- **Expiry and attempt limit:** stops slow guessing and limits brute force.
- **Constant-time comparison** (`hmac.compare_digest`) avoids timing side-channels.

## How the Code Works

File: `2_CAPTCHA/captcha.py` (needs `pillow` and `numpy`).

### Settings
```python
CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZabdefghjkmnpqrstuvwxyz23456789"   # no 0 O 1 l I c o
LENGTH = 6
EXPIRY_SECONDS = 120
MAX_ATTEMPTS = 3
SERVER_KEY = secrets.token_bytes(32)          # secret known only to the server
```
`secrets` (not `random`) is used so the text is unpredictable. The key is created at start-up and kept only in memory.

### Generation: `random_text()` and `draw_captcha(text)`
1. Create a light random background and sprinkle 600 noise dots.
2. For each character: choose a random font (tries Arial Bold, Georgia, Verdana, Courier, DejaVu; falls back to Pillow's default), random size 34-46, dark random colour, draw it on its own small transparent tile, **rotate by -30 to +30 degrees**, paste at a jittered position.
3. **Wave distortion:** every pixel column is shifted up/down along a sine wave using NumPy.
```python
for col in range(width):
    arr[:, col] = np.roll(arr[:, col], int(amp * math.sin(2 * math.pi * col / period + phase)), axis=0)
```
4. Draw 4 random lines and 2 arcs across the text, then apply a small smoothing filter.

### Verification: `CaptchaStore`
It imitates a server session store. `pending` maps `captcha_id -> {hash, created, attempts}`.

- `create()` makes an 8-byte random hex ID, the text, and stores **only** the HMAC. The plain text is returned to the caller so the image can be drawn (and for the test).
- `answer_hash()` computes `HMAC-SHA256(SERVER_KEY, "<id>:<normalised answer>")`. `normalise()` removes spaces and lower-cases, so the check is case-insensitive.
- `verify()` applies the rules in this order:

| Step | Result message |
| --- | --- |
| ID not found (never existed / already used / deleted) | "Unknown or already used CAPTCHA" |
| Older than 120 s | "CAPTCHA expired" (entry deleted) |
| Attempt counter +1; HMAC equal | "Correct - you are human" (entry **deleted** = one-time use) |
| Third wrong attempt | "Too many wrong attempts" (entry deleted) |
| Otherwise | "Wrong answer (n attempt(s) left)" |

```python
if hmac.compare_digest(entry["hash"], answer_hash(captcha_id, user_input)):
    del self.pending[captcha_id]                       # one-time use
    return True, "Correct - you are human"
```

### Self-test and interactive mode
`self_test()` checks: plain text not stored, case/space tolerance, replay fails, correct answer after 3 wrong tries still fails, expired CAPTCHA fails (by passing a fake `now` in the past), 2000 texts are unique with no look-alike characters. It saves `captcha_sample.png` and a 3x3 sheet `captcha_examples.png`. `interactive()` saves `captcha.png`, opens it and asks you to type the text.

## How to Run and Expected Output

```bash
pip install pillow numpy
python LP4/CSDF/2_CAPTCHA/captcha.py            # interactive: image opens, type the text
python LP4/CSDF/2_CAPTCHA/captcha.py --test     # automatic self-test
```

Real output of `--test`:

```
1. Correct answer (different case, extra spaces): True  Correct - you are human
2. Replay the same solved CAPTCHA             : False  Unknown or already used CAPTCHA - request a new one
3. Correct answer after 3 wrong tries        : False  Unknown or already used CAPTCHA - request a new one
   messages: ['Wrong answer (2 attempt(s) left)', 'Wrong answer (1 attempt(s) left)', 'Too many wrong attempts - request a new one']
4. Correct answer after expiry                : False  CAPTCHA expired - request a new one
5. 2000 random texts: all unique, no look-alike characters (32^6 = 1,073,741,824 possible answers)
Self-test passed.
```

Why "32^6": since answers are case-insensitive, the 54 characters collapse to 32 distinct symbols, so there are about 1.07 billion possible answers.

The generated pictures `captcha_sample.png` and `captcha_examples.png` are in the `2_CAPTCHA` folder; show them in the lab report.

## Related Concepts and Real-World Tools

- **Google reCAPTCHA (v2 checkbox / image tiles, v3 invisible score)**, **hCaptcha**, **Cloudflare Turnstile**.
- **Rate limiting, account lockout, and Web Application Firewalls** work together with CAPTCHA.
- **CAPTCHA farms and ML solvers:** services employ humans or neural networks to solve CAPTCHAs, so CAPTCHA is a speed-bump, not a complete defence.
- **Accessibility:** audio alternatives and WCAG guidelines.
- **Stateless variant:** instead of a server store, the server may send the ID plus an HMAC-signed token with an expiry time inside it.
- **Python libraries:** `captcha`, `claptcha`, `multicolorcaptcha`.
- **IT Act 2000:** automated brute-force login attempts fall under Section 43 / 66 (unauthorised access), which is why such protections are expected.

## Viva Questions

1. **What does CAPTCHA stand for and what is it used for?** Completely Automated Public Turing test to tell Computers and Humans Apart. It blocks bots from login, registration and form abuse.
2. **Why do you store an HMAC instead of the answer?** If the store or database leaks, the attacker still cannot read the answers. HMAC needs the secret server key, so he cannot even pre-compute guesses.
3. **What is the difference between a hash and an HMAC?** A hash has no key, so anyone can compute it. An HMAC mixes in a secret key so only the key holder can produce or verify it.
4. **What is a replay attack and how is it prevented here?** Re-sending an old valid answer. The entry is deleted after the first successful verification, so a second try gets "Unknown or already used".
5. **Why is the CAPTCHA ID mixed into the HMAC?** So the same text produces a different hash each time and a hash from one CAPTCHA cannot be reused for another.
6. **Why are expiry and the 3-attempt limit needed?** They limit how long and how many times an attacker can guess, so brute-forcing a 6-character answer becomes impractical.
7. **Why remove characters like 0, O, 1, l, I?** Humans confuse them, so removing them reduces false failures without helping bots much.
8. **How do the noise and wave distortion help?** They break the clean character shapes that OCR depends on, while humans can still recognise the characters.
9. **Why use `secrets` rather than `random`?** `secrets` uses the operating system's cryptographically secure generator, so the text and IDs cannot be predicted.
10. **Can a CAPTCHA be broken?** Yes: modern OCR/ML and human CAPTCHA farms can solve many of them. So it is combined with rate limiting, lockouts and behavioural checks.
