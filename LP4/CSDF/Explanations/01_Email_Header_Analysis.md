# Assignment 1: Email Header Analysis (Tracking Emails and Investigating Email Crimes)

## Aim

Write a program for Tracking Emails and Investigating Email Crimes, i.e. write a program to analyze an e-mail header.

## Theory and Fundamentals

### Anatomy of an e-mail
An e-mail has two parts: the **body** (what you read) and the **headers** (technical details added by the sender's software and every server on the way). Headers are plain text lines of the form `Name: value`. The body can be lied about easily; headers added by *other people's servers* are much harder to fake, so they are the main evidence.

### Important headers

| Header | Meaning | Can the sender fake it? |
| --- | --- | --- |
| `From` | Address (and display name) the reader sees | Yes, trivially |
| `Return-Path` | Address where bounces go (the SMTP envelope sender) | Yes, but it often exposes the real sending server |
| `Reply-To` | Where your reply will go | Yes. Fraudsters set it to their own mailbox |
| `Message-ID` | Unique ID created by the *sending* server (`<id@domain>`) | Yes, but a mismatch with `From` is a clue |
| `Date` | Time set by the sender's computer | Yes |
| `Received` | One line added by **each** server that handled the mail | The top lines (added by your own provider) are trustworthy |
| `X-Mailer` | Software used to write the mail (e.g. PHPMailer) | Yes |
| `Authentication-Results` | SPF / DKIM / DMARC verdicts written by the receiving server | Trustworthy if added by your own server |

### The Received chain
Every server **adds** a `Received:` header at the **top**. So the newest hop is at the top and the oldest (closest to the sender) is at the bottom. An investigator reads from **bottom to top** to follow the route. The first *public* IP address in the chain is usually the **originating IP**, which can then be looked up in WHOIS / AbuseIPDB to find the ISP or hosting company. Differences between hop timestamps show delays; timestamps that go backwards suggest forged headers.

### SPF, DKIM, DMARC
- **SPF (Sender Policy Framework):** the domain owner publishes in DNS the list of IPs allowed to send mail for the domain. Result: `pass`, `fail`, `softfail`, `none`.
- **DKIM (DomainKeys Identified Mail):** the sending server signs the message with a private key; the receiver checks the signature using the public key in DNS. Proves the message was not changed and came from that domain.
- **DMARC:** a policy that says what to do when SPF/DKIM fail *and* do not align with the visible `From` domain (none / quarantine / reject).

### Attacks to know
- **Email spoofing:** forging the `From` address so the mail appears to come from someone trusted.
- **Phishing:** fake mail (bank, KYC, lottery) that tricks the user into giving passwords or money, usually through a fake login link.
- **Business Email Compromise / CEO fraud:** the attacker pretends to be a senior person and asks staff to pay money or buy gift cards.
- **Deceptive links:** the visible text says `www.onlinesbi.sbi` but the real `href` points somewhere else (often a raw IP address).

### Legal angle (India)
Phishing and impersonation are covered by the IT Act 2000: Section 66C (identity theft), 66D (cheating by personation using a computer resource) and 43/66 (unauthorised access / damage). Header evidence must be preserved with hashes and a chain of custody (see Assignment 11).

## How the Code Works

File: `1_EmailHeaderAnalysis/email_header_analyzer.py`. It uses only the Python standard library (`email`, `ipaddress`, `re`).

**Data flow:** `.eml` file -> `email.message_from_binary_file` -> `trace_route` -> `originating_ip` -> `auth_results` -> `check` (findings with points) -> score and verdict.

### 1. Parsing and route tracing
`trace_route(msg)` reads all `Received` headers in **reverse** (oldest first), flattens whitespace and applies a regular expression to get `from`, `by`, the IP in brackets and the date.

```python
for raw in reversed(msg.get_all("Received", [])):          # oldest (sender side) first
    text = " ".join(str(raw).split())
    m = RECEIVED_RE.search(text)
```

**Which IP is trusted?** The text right after `from` is the name the *sender* claimed (the HELO), so it can be faked. The part in `( … )` was written by the *receiving* server from the real connection, so the code prefers IPs found inside parentheses and only falls back to the claimed name:

```python
sender_part = text[m.start("from"):m.start("by")]
verified = " ".join(re.findall(r"\(([^)]*)\)", sender_part))
ips = [ip for ip in IP_RE.findall(verified) or IP_RE.findall(sender_part) if ip_kind(ip) != "invalid"]
```

Example: `from [192.168.1.23] (static.45-112.isp.net.in [49.36.112.45])` gives `49.36.112.45` (the sender's real public IP), not the private address it claimed.

The delay of each hop is the difference between its timestamp and the previous hop's. `ip_kind()` classifies every IP as `public`, `private`, `internal` or `invalid` using the `ipaddress` module.

### 2. Originating IP
`originating_ip()` first looks at `X-Originating-IP` / `X-Sender-IP` (added by some webmail services). If these are absent it returns the **first public IP** in the Received chain. Private addresses (10.x, 192.168.x) are skipped.

### 3. Authentication
`auth_results()` searches `Authentication-Results` and `Received-SPF` for `spf=`, `dkim=`, `dmarc=` and returns e.g. `{"SPF": "fail", "DKIM": "none", "DMARC": "fail"}`.

### 4. Spoofing checks and scoring
`check()` returns a list of `(points, text)` findings. The score is the sum, capped at 100.

| Check | Points |
| --- | --- |
| `Return-Path`, `Reply-To` or `Sender` domain differs from `From` domain (each) | 25 |
| `Message-ID` domain differs from `From` domain | 10 |
| SPF or DMARC `fail` / `softfail` / `permerror` | 30 each |
| DKIM `fail` / `softfail` / `permerror` | 20 |
| Authentication result missing (`none`) | 5 each |
| Display name contains an e-mail address of another domain | 20 |
| Display name claims a brand (paypal, sbi, hdfc, icici, amazon, microsoft, google, apple) but domain does not contain it | 20 |
| 2 or more pressure/financial words (urgent, kyc, gift card ...) | 10 |
| Link text shows one domain but `href` goes to another | 25 |
| Link points to a bare IP address | 15 |
| A hop timestamp goes backwards by more than 60 s | 15 |

`base_domain()` reduces `mail.google.com` to `google.com` (and handles `.co.in`) so that sub-domains do not cause false alarms.

```python
score = min(100, sum(p for p, _ in findings))
verdict = "SAFE" if score < 25 else "SUSPICIOUS" if score < 60 else "SPOOFED / PHISHING"
```

### 5. Demo mails
The script contains three mails as strings and writes them to `samples/`:
- `genuine.eml`: a real-looking Gmail message, SPF/DKIM/DMARC all pass.
- `phishing_bank.eml`: fake "SBI Alerts", Return-Path from a `.ru` host, Reply-To on protonmail, fake link to a bare IP.
- `ceo_fraud.eml`: display name is the principal's address but the real sender is a Gmail account; asks for gift cards.

With `--demo` the program ends with `assert`s on the three verdicts and the three originating IPs (the self-check).

## How to Run and Expected Output

```bash
pip install -r LP4/CSDF/requirements.txt
python LP4/CSDF/1_EmailHeaderAnalysis/email_header_analyzer.py --demo     # 3 sample mails
python LP4/CSDF/1_EmailHeaderAnalysis/email_header_analyzer.py mail.eml   # your own mail
```

To get headers of a real mail: Gmail -> three dots -> *Show original*; Outlook -> File -> Properties -> *Internet headers*.

Real output (trimmed):

```
EMAIL HEADER ANALYSIS: genuine.eml
Hop 1: [192.168.1.23]  -> smtp.gmail.com        IP 49.36.112.45 (public)
Hop 2: mail-yw1-f170.google.com -> mx.college.edu.in   IP 209.85.128.170 (public)  +4s
Originating IP : 49.36.112.45   [first public IP in Received chain]
SPF: PASS   DKIM: PASS   DMARC: PASS
No suspicious signs
Risk score: 0/100   VERDICT: SAFE

EMAIL HEADER ANALYSIS: phishing_bank.eml
Originating IP : 185.220.101.45
SPF: FAIL   DKIM: NONE   DMARC: FAIL
[+25] Return-Path domain 'cheaphost.ru' differs from From domain 'sbi.co.in'
[+25] Link text shows 'www.onlinesbi.sbi' but goes to '185.220.101.45'
Risk score: 100/100   VERDICT: SPOOFED / PHISHING

EMAIL HEADER ANALYSIS: ceo_fraud.eml
Hop 1: unknown  -> mx.college.edu.in   IP 103.21.58.9 (public)
Originating IP : 103.21.58.9   [first public IP in Received chain]
...
Self-check passed: genuine mail SAFE, both fraud mails detected, all 3 originating IPs traced.
```

Notes for the viva demonstration:
- In `ceo_fraud.eml` the sender's server said `HELO college.edu.in` (pretending to be the college), but the receiving server recorded the real IP `103.21.58.9` in brackets. That recorded IP is what the tool reports, which is exactly why the claimed name must never be trusted.
- The scores are teaching heuristics, not a standard.

## Related Concepts and Real-World Tools

- **MXToolbox Email Header Analyzer:** paste headers online, shows hop delays and SPF/DKIM/DMARC.
- **Google Admin Toolbox "Messageheader"** and **Gmail "Show original"**.
- **WHOIS / AbuseIPDB / IPinfo:** identify the owner of the originating IP.
- **Wireshark / mail-server logs:** to confirm the SMTP session.
- **Email security gateways** (Proofpoint, Microsoft Defender for Office 365) apply the same checks at scale.
- **ARC, BIMI, TLS reporting (MTA-STS):** newer standards in the same family.
- **IT Act 2000:** Sections 43, 66, 66C, 66D; reporting at cybercrime.gov.in (helpline 1930).
- An investigator must also obtain the mail from the **server** (not only the user's inbox), because the user's copy may be edited.

## Viva Questions

1. **Why do we read the Received headers from bottom to top?** Each server adds its header at the top, so the bottom one was added first, closest to the sender. Reading upward follows the real path.
2. **Can the From address be trusted?** No. It is set by the sender's software and can be forged. We compare it with Return-Path, Reply-To, Message-ID and SPF/DKIM/DMARC results.
3. **What is the difference between SPF and DKIM?** SPF checks that the sending IP is authorised for the domain; DKIM checks a cryptographic signature on the message. DMARC combines them with a policy.
4. **How does the program find the originating IP?** It uses `X-Originating-IP` if present, otherwise the first public IP (not 10.x / 192.168.x) in the Received chain.
5. **What is spoofing and how does it differ from phishing?** Spoofing is forging the sender identity; phishing is the fraud that uses it to steal credentials or money. Phishing usually uses spoofing.
6. **What does a Return-Path / Reply-To mismatch indicate?** The replies or bounces go to a different domain from the one shown in From, a common sign of fraud. The tool adds 25 points for each.
7. **How does the tool detect a deceptive link?** It extracts every `<a href>`, compares the domain in the visible text with the domain in the `href`, and also flags links to bare IPs.
8. **What does a hop timestamp going backwards mean?** Servers keep roughly correct clocks, so a big backwards jump suggests a forged Received line. The tool adds 15 points.
9. **Why is a header analysis alone not enough in court?** The headers must be collected from the mail server, hashed and kept with a chain of custody, and the IP owner must be confirmed through the ISP using a legal request.
10. **Is a SAFE verdict a guarantee?** No. A compromised genuine account passes SPF/DKIM/DMARC; the score is only a heuristic.
