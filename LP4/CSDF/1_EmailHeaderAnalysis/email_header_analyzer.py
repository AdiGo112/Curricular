# =========================================================
# ASSIGNMENT 1
# Tracking Emails and Investigating Email Crimes
# (E-mail Header Analysis)
# =========================================================
#
# Every server that handles an e-mail adds a "Received:"
# header ON TOP of the others. Reading them bottom-to-top
# gives the real path of the mail, even when the "From:"
# line is fake.
#
# This program reads a .eml file (or pasted headers) and:
#   1. Lists the basic headers (From, To, Subject, Date, ...)
#   2. Traces the mail route hop by hop with delay at each hop
#   3. Finds the ORIGINATING IP (first public IP in the chain)
#   4. Reads SPF / DKIM / DMARC results (Authentication-Results)
#   5. Checks for signs of spoofing / phishing:
#        From vs Return-Path / Reply-To domain mismatch,
#        Message-ID domain mismatch, failed authentication,
#        display-name tricks, urgent/financial keywords,
#        links whose text and target differ
#   6. Gives a risk score and a verdict
#
# =========================================================
# HOW TO USE
# =========================================================
#
#   python email_header_analyzer.py --demo      (analyse 3 sample mails)
#   python email_header_analyzer.py mail.eml    (your own mail)
#
# To get a real mail's headers:
#   Gmail   : open mail > three dots > "Show original" > Download
#   Outlook : open mail > File > Properties > Internet headers
#
# =========================================================

import argparse
import email
import ipaddress
import os
import re
import sys
from email import policy
from email.utils import parseaddr, parsedate_to_datetime

URGENT_WORDS = ["urgent", "immediately", "verify your account", "suspended", "password",
                "bank", "lottery", "winner", "prize", "invoice", "payment", "gift card", "kyc"]


# =========================================================
# HELPERS
# =========================================================

def domain_of(address):
    addr = parseaddr(address or "")[1]
    return addr.split("@")[-1].lower() if "@" in addr else ""


def base_domain(domain):
    """mail.google.com -> google.com (good enough for comparison)."""
    parts = domain.split(".")
    if len(parts) >= 3 and parts[-2] in ("co", "com", "org", "net", "ac", "gov") and len(parts[-1]) == 2:
        return ".".join(parts[-3:])          # e.g. company.co.in
    return ".".join(parts[-2:])


def ip_kind(ip):
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return "invalid"
    if addr.is_private:
        return "private"
    if addr.is_loopback or addr.is_reserved or addr.is_link_local:
        return "internal"
    return "public"


# =========================================================
# 2-3. ROUTE TRACING
# =========================================================

RECEIVED_RE = re.compile(
    r"from\s+(?P<from>\S+)(?:\s+\((?P<info>[^)]*)\))?.*?by\s+(?P<by>\S+).*?;\s*(?P<date>.+)$",
    re.IGNORECASE | re.DOTALL)
IP_RE = re.compile(r"\[?((?:\d{1,3}\.){3}\d{1,3}|[0-9a-f]*:[0-9a-f:]+)\]?", re.IGNORECASE)


def trace_route(msg):
    hops = []
    for raw in reversed(msg.get_all("Received", [])):          # oldest (sender side) first
        text = " ".join(str(raw).split())
        m = RECEIVED_RE.search(text)
        if not m:
            continue
        # IPs inside (...) were recorded by the RECEIVING server, so they can be trusted;
        # the name right after "from" is whatever the sender claimed (HELO), so use it only as a fallback.
        # e.g. "from [192.168.1.23] (static.isp.net.in [49.36.112.45])" -> 49.36.112.45
        #      "from unknown (HELO college.edu.in) (103.21.58.9)"         -> 103.21.58.9
        sender_part = text[m.start("from"):m.start("by")]
        verified = " ".join(re.findall(r"\(([^)]*)\)", sender_part))
        ips = [ip for ip in IP_RE.findall(verified) or IP_RE.findall(sender_part) if ip_kind(ip) != "invalid"]
        try:
            when = parsedate_to_datetime(m.group("date").strip())
        except (TypeError, ValueError):
            when = None
        hops.append({"from": m.group("from"), "by": m.group("by"), "ip": ips[0] if ips else "", "time": when})
    for prev, cur in zip(hops, hops[1:]):
        if prev["time"] and cur["time"]:
            cur["delay"] = (cur["time"] - prev["time"]).total_seconds()
    return hops


def originating_ip(msg, hops):
    for header in ("X-Originating-IP", "X-Sender-IP"):        # some webmail services add this
        if msg.get(header):
            ip = msg[header].strip("[] ")
            if ip_kind(ip) == "public":
                return ip, header
    for hop in hops:
        if hop["ip"] and ip_kind(hop["ip"]) == "public":
            return hop["ip"], "first public IP in Received chain"
    return "", "not found"


# =========================================================
# 4. AUTHENTICATION RESULTS
# =========================================================

def auth_results(msg):
    text = " ".join(str(h) for h in msg.get_all("Authentication-Results", []))
    text += " " + str(msg.get("Received-SPF", ""))
    results = {}
    for mech in ("spf", "dkim", "dmarc"):
        m = re.search(rf"{mech}\s*=\s*(\w+)", text, re.IGNORECASE)
        if m:
            results[mech.upper()] = m.group(1).lower()
        elif mech == "spf" and msg.get("Received-SPF"):
            results["SPF"] = str(msg["Received-SPF"]).split()[0].lower()
        else:
            results[mech.upper()] = "none"
    return results


# =========================================================
# 5. SPOOFING / PHISHING CHECKS
# =========================================================

def body_text(msg):
    part = msg.get_body(preferencelist=("html", "plain"))
    return part.get_content() if part else ""


def check(msg, hops, auth):
    findings = []                       # (points, text)
    from_dom = domain_of(msg["From"])
    display = parseaddr(msg["From"] or "")[0]

    for header in ("Return-Path", "Reply-To", "Sender"):
        dom = domain_of(msg[header])
        if dom and from_dom and base_domain(dom) != base_domain(from_dom):
            findings.append((25, f"{header} domain '{dom}' differs from From domain '{from_dom}'"))

    mid = msg.get("Message-ID", "")
    mid_dom = mid.strip("<>").split("@")[-1].lower() if "@" in mid else ""
    if mid_dom and from_dom and base_domain(mid_dom) != base_domain(from_dom):
        findings.append((10, f"Message-ID created by '{mid_dom}', not by '{from_dom}'"))

    for mech, result in auth.items():
        if result in ("fail", "softfail", "permerror"):
            findings.append((30 if mech != "DKIM" else 20, f"{mech} {result.upper()}: sender not authorised"))
        elif result == "none":
            findings.append((5, f"No {mech} result"))

    if display and "@" in display and domain_of(display) != from_dom:
        findings.append((20, f"Display name shows another address: '{display}'"))
    for brand in ("paypal", "sbi", "hdfc", "icici", "amazon", "microsoft", "google", "apple"):
        if brand in display.lower() and brand not in from_dom:
            findings.append((20, f"Display name claims '{brand}' but mail is from '{from_dom}'"))

    body = body_text(msg)
    subject = str(msg["Subject"] or "")
    words = [w for w in URGENT_WORDS if w in (subject + " " + body).lower()]
    if len(words) >= 2:
        findings.append((10, f"Pressure / financial words: {', '.join(words)}"))

    for href, text in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', body, re.IGNORECASE | re.DOTALL):
        shown = re.search(r"[a-z0-9.-]+\.[a-z]{2,}", text.lower())
        target = re.search(r"https?://([^/:]+)", href.lower())
        if shown and target and base_domain(shown.group()) != base_domain(target.group(1)):
            findings.append((25, f"Link text shows '{shown.group()}' but goes to '{target.group(1)}'"))
        if target and re.fullmatch(r"[\d.]+", target.group(1)):
            findings.append((15, f"Link points to a bare IP address: {target.group(1)}"))

    if any(h.get("delay", 0) < -60 for h in hops):
        findings.append((15, "Hop timestamps go backwards (headers may be forged)"))
    return findings


# =========================================================
# REPORT
# =========================================================

def analyse(path):
    with open(path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    hops = trace_route(msg)
    origin, how = originating_ip(msg, hops)
    auth = auth_results(msg)
    findings = check(msg, hops, auth)
    score = min(100, sum(p for p, _ in findings))
    verdict = "SAFE" if score < 25 else "SUSPICIOUS" if score < 60 else "SPOOFED / PHISHING"

    out = ["=" * 72, f" EMAIL HEADER ANALYSIS: {os.path.basename(path)}", "=" * 72]
    for h in ("From", "To", "Subject", "Date", "Return-Path", "Reply-To", "Message-ID", "X-Mailer"):
        if msg[h]:
            out.append(f"{h:12}: {msg[h]}")

    out.append("\n--- Route (sender first) ---")
    for i, hop in enumerate(hops, 1):
        delay = f"+{hop['delay']:.0f}s" if "delay" in hop else ""
        ip = f"{hop['ip']} ({ip_kind(hop['ip'])})" if hop["ip"] else "-"
        out.append(f"Hop {i}: {hop['from']:28} -> {hop['by']:28} IP {ip:24} {delay}")
    out.append(f"\nOriginating IP : {origin or 'unknown'}   [{how}]")
    if origin:
        out.append(f"  Look it up   : https://whois.domaintools.com/{origin}  |  https://www.abuseipdb.com/check/{origin}")

    out.append("\n--- Authentication ---")
    out.append("   ".join(f"{k}: {v.upper()}" for k, v in auth.items()))

    out.append("\n--- Findings ---")
    out += [f"[+{p:2}] {text}" for p, text in findings] or ["No suspicious signs"]
    out.append(f"\nRisk score: {score}/100   VERDICT: {verdict}")
    return "\n".join(out), verdict


# =========================================================
# DEMO MAILS
# =========================================================

GENUINE = """Received: from mail-yw1-f170.google.com (mail-yw1-f170.google.com [209.85.128.170])
	by mx.college.edu.in (Postfix) with ESMTPS id 4A1B2C3D;
	Mon, 2 Nov 2026 10:15:09 +0530
Received: from [192.168.1.23] (static.45-112.isp.net.in [49.36.112.45])
	by smtp.gmail.com with ESMTPSA id k12sm;
	Mon, 2 Nov 2026 10:15:05 +0530
Authentication-Results: mx.college.edu.in; spf=pass smtp.mailfrom=gmail.com;
	dkim=pass header.d=gmail.com; dmarc=pass header.from=gmail.com
Return-Path: <priya.sharma@gmail.com>
From: Priya Sharma <priya.sharma@gmail.com>
To: aditya@college.edu.in
Subject: Notes for tomorrow's CSDF practical
Date: Mon, 2 Nov 2026 10:15:00 +0530
Message-ID: <CAF8x9Q@mail.gmail.com>
Content-Type: text/plain; charset=utf-8

Hi, I have attached the notes for the practical. See you tomorrow.
"""

PHISHING = """Received: from mx.college.edu.in (mx.college.edu.in [10.0.0.5])
	by inbox.college.edu.in (Postfix); Tue, 3 Nov 2026 02:41:30 +0530
Received: from vps-77.cheaphost.ru (vps-77.cheaphost.ru [185.220.101.45])
	by mx.college.edu.in (Postfix) with ESMTP id 9F8E7D;
	Tue, 3 Nov 2026 02:41:28 +0530
Authentication-Results: mx.college.edu.in; spf=fail smtp.mailfrom=sbi.co.in;
	dkim=none; dmarc=fail header.from=sbi.co.in
Return-Path: <bounce@cheaphost.ru>
Reply-To: kyc.update.desk@protonmail.com
From: "SBI Alerts" <alerts@sbi.co.in>
To: aditya@college.edu.in
Subject: URGENT: Your account will be suspended - complete KYC immediately
Date: Tue, 3 Nov 2026 02:41:00 +0530
Message-ID: <20261103.4471@vps-77.cheaphost.ru>
X-Mailer: PHPMailer 5.2.1
Content-Type: text/html; charset=utf-8

<p>Dear customer, your bank account will be suspended in 24 hours.</p>
<p>Verify your account and password here:
<a href="http://185.220.101.45/sbi/login.php">https://www.onlinesbi.sbi</a></p>
"""

SPOOFED_INTERNAL = """Received: from unknown (HELO college.edu.in) (103.21.58.9)
	by mx.college.edu.in with SMTP; Wed, 4 Nov 2026 11:05:12 +0530
Authentication-Results: mx.college.edu.in; spf=softfail smtp.mailfrom=college.edu.in;
	dkim=none; dmarc=fail header.from=college.edu.in
From: "principal@college.edu.in" <principal.office.desk@gmail.com>
To: accounts@college.edu.in
Subject: Urgent payment - gift cards needed
Date: Wed, 4 Nov 2026 11:05:00 +0530
Message-ID: <a81f@103.21.58.9>
Content-Type: text/plain; charset=utf-8

I am in a meeting. Buy 10 gift cards for the guests and send the codes immediately. Payment will be reimbursed.
"""


def make_demo(folder):
    os.makedirs(folder, exist_ok=True)
    paths = []
    for name, text in (("genuine.eml", GENUINE), ("phishing_bank.eml", PHISHING), ("ceo_fraud.eml", SPOOFED_INTERNAL)):
        path = os.path.join(folder, name)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        paths.append(path)
    return paths


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="E-mail header analysis tool")
    parser.add_argument("files", nargs="*", help=".eml files")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    files = make_demo(os.path.join(here, "samples")) if args.demo else args.files
    if not files:
        parser.print_help()
        sys.exit(1)

    verdicts, reports = {}, {}
    for path in files:
        report, verdict = analyse(path)
        verdicts[os.path.basename(path)] = verdict
        reports[os.path.basename(path)] = report
        print(report + "\n")

    if args.demo:
        assert verdicts == {"genuine.eml": "SAFE", "phishing_bank.eml": "SPOOFED / PHISHING",
                            "ceo_fraud.eml": "SPOOFED / PHISHING"}, verdicts
        # the sender's real IP, not the mail servers' or a private LAN address
        for name, ip in (("genuine.eml", "49.36.112.45"), ("phishing_bank.eml", "185.220.101.45"),
                         ("ceo_fraud.eml", "103.21.58.9")):
            assert f"Originating IP : {ip} " in reports[name], (name, ip)
        print("Self-check passed: genuine mail SAFE, both fraud mails detected, all 3 originating IPs traced.")
