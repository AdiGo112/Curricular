# =========================================================
# MINI PROJECT 11
# Cyber Crime Analysis System using Forensic Techniques
# (compared w.r.t. Confidentiality, Integrity, Availability)
# =========================================================
#
# CASE: An employee is suspected of stealing the client
# database and sending it outside the company.
#
# PHASE 1  Acquisition   : evidence is copied, made read-only
#                          and hashed (SHA-256 manifest)
# PHASE 2  Protection    : six forensic techniques are applied
#     T1 Hashing (SHA-256)              -> Integrity
#     T2 Chain of custody with HMAC     -> Integrity, accountability
#     T3 Write blocking (read-only)     -> Integrity
#     T4 Encryption (AES / Fernet)      -> Confidentiality
#     T5 Role based access control      -> Confidentiality
#     T6 Redundant backups + self-heal  -> Availability
# PHASE 3  Analysis      : known-malware hash matching, file
#                          signature check, keyword search,
#                          event timeline
# PHASE 4  Attacks       : evidence is tampered, logs forged,
#                          vault deleted, outsider tries access.
#                          Each technique either detects /
#                          prevents the attack or not.
# PHASE 5  Comparison    : CIA table + measured time cost,
#                          saved to comparison_report.txt
#
# =========================================================
# HOW TO RUN
# =========================================================
#
#   pip install cryptography
#   python forensic_system.py
#
# =========================================================

import hashlib
import hmac
import json
import os
import shutil
import stat
import sys
import time

from cryptography.fernet import Fernet, InvalidToken

HERE = os.path.dirname(os.path.abspath(__file__))
SCENE = os.path.join(HERE, "crime_scene")      # suspect's laptop (source)
CASE = os.path.join(HERE, "case_2026_041")     # investigator's case folder

# ponytail: keys kept in memory for the demo; a real lab stores them in an HSM / key vault
CUSTODY_KEY = os.urandom(32)
VAULT_KEY = Fernet.generate_key()

ROLES = {"insp_patil": "investigator", "clerk_joshi": "viewer"}
PERMISSIONS = {"investigator": {"read", "decrypt", "analyse"}, "viewer": {"read"}}

KEYWORDS = ["confidential", "client", "usb", "delete", "transfer", "password"]

SIGNATURES = {b"PK\x03\x04": "ZIP", b"\xff\xd8\xff": "JPEG", b"%PDF": "PDF", b"MZ": "EXE"}
EXT_TYPES = {".zip": "ZIP", ".jpg": "JPEG", ".pdf": "PDF", ".exe": "EXE"}

KEYLOGGER = b"MZ\x90\x00 fake keylogger build 2.1 -- captures keystrokes" + b"\x00" * 32
KNOWN_BAD_HASHES = {hashlib.sha256(KEYLOGGER).hexdigest(): "Keylogger (in known-bad hash list)"}


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def remove_folder(path):
    """Delete a folder even if it holds read-only (write-blocked) files."""
    def make_writable(func, p, _):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    if os.path.exists(path):
        # Python 3.12+ calls it onexc, older versions onerror
        key = "onexc" if sys.version_info >= (3, 12) else "onerror"
        shutil.rmtree(path, **{key: make_writable})


def title(text):
    print("\n" + "=" * 70 + f"\n {text}\n" + "=" * 70)


# =========================================================
# SAMPLE CRIME SCENE
# =========================================================

def create_crime_scene():
    remove_folder(SCENE)
    files = {
        "emails/mail_01.eml":
            "From: rahul@company.com\nTo: buyer.x@protonmail.com\nDate: 2026-10-20 22:31\n"
            "Subject: data\n\nAs discussed, the confidential client list is attached. "
            "Transfer the money to my account and delete this mail.\n",
        "emails/mail_02.eml":
            "From: hr@company.com\nTo: rahul@company.com\nDate: 2026-10-18 10:00\n"
            "Subject: Leave approved\n\nYour leave for 21-25 Oct is approved.\n",
        "logs/auth.log":
            "2026-10-20 22:05:11 user=rahul action=LOGIN host=WS-14\n"
            "2026-10-20 22:12:40 user=rahul action=USB_INSERT device=SanDisk_32GB\n"
            "2026-10-20 22:14:03 user=rahul action=FILE_COPY file=clients.csv dest=E:\\\n"
            "2026-10-20 22:29:57 user=rahul action=FILE_RENAME file=clients.zip new=holiday.jpg\n"
            "2026-10-20 22:40:22 user=rahul action=LOGOUT host=WS-14\n"
            "2026-10-20 09:01:15 user=priya action=LOGIN host=WS-02\n",
        "docs/clients.csv": "id,name,phone,card\n1,Asha Rao,98XXXXXX01,4111-XXXX\n2,Vikram S,98XXXXXX02,5500-XXXX\n",
    }
    for rel, text in files.items():
        path = os.path.join(SCENE, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)
    with open(os.path.join(SCENE, "docs/holiday.jpg"), "wb") as f:     # ZIP disguised as photo
        f.write(b"PK\x03\x04clients.csv" + b"\x00" * 64)
    os.makedirs(os.path.join(SCENE, "tools"), exist_ok=True)
    with open(os.path.join(SCENE, "tools/svchost_update.exe"), "wb") as f:
        f.write(KEYLOGGER)


# =========================================================
# T2: CHAIN OF CUSTODY (each entry signed with HMAC and
#     linked to the previous one, like a mini blockchain)
# =========================================================

class CustodyLog:
    def __init__(self, path):
        self.path = path
        self.entries = []

    def add(self, who, action, detail=""):
        prev = self.entries[-1]["mac"] if self.entries else "0" * 64
        entry = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "who": who, "action": action,
                 "detail": detail, "prev": prev}
        entry["mac"] = self._mac(entry)
        self.entries.append(entry)
        with open(self.path, "w") as f:
            json.dump(self.entries, f, indent=1)

    @staticmethod
    def _mac(entry):
        body = json.dumps({k: entry[k] for k in ("time", "who", "action", "detail", "prev")}, sort_keys=True)
        return hmac.new(CUSTODY_KEY, body.encode(), hashlib.sha256).hexdigest()

    def verify(self):
        with open(self.path) as f:
            entries = json.load(f)
        prev = "0" * 64
        for i, e in enumerate(entries):
            if e["prev"] != prev or not hmac.compare_digest(e["mac"], self._mac(e)):
                return False, i
            prev = e["mac"]
        # Links alone cannot catch entries cut off the END of the log.
        # The latest MAC ("head") is also kept by the supervisor, so compare with it.
        head = self.entries[-1]["mac"] if self.entries else "0" * 64
        if prev != head:
            return False, len(entries)
        return True, None


# =========================================================
# PHASE 1 + 2: ACQUISITION AND PROTECTION
# =========================================================

def acquire(custody, timings):
    remove_folder(CASE)
    evidence = os.path.join(CASE, "evidence")

    t = time.perf_counter()
    shutil.copytree(SCENE, evidence)
    manifest = {}
    for root, _, files in os.walk(evidence):
        for name in files:
            path = os.path.join(root, name)
            manifest[os.path.relpath(path, evidence)] = sha256_file(path)          # T1
    with open(os.path.join(CASE, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    timings["T1 Hashing (SHA-256)"] = time.perf_counter() - t

    t = time.perf_counter()
    for root, _, files in os.walk(evidence):                                       # T3
        for name in files:
            os.chmod(os.path.join(root, name), stat.S_IREAD)
    timings["T3 Write blocking"] = time.perf_counter() - t

    custody.add("insp_patil", "ACQUIRED", f"{len(manifest)} files from suspect laptop WS-14")
    custody.add("insp_patil", "HASHED", "SHA-256 manifest created")
    print(f"Acquired {len(manifest)} files, hashed and made read-only.")
    return evidence, manifest


def build_vault(evidence, custody, timings):
    t = time.perf_counter()
    fernet = Fernet(VAULT_KEY)                                                     # T4
    archive = shutil.make_archive(os.path.join(CASE, "evidence_bundle"), "zip", evidence)
    with open(archive, "rb") as f:
        token = fernet.encrypt(f.read())
    os.remove(archive)
    vault = os.path.join(CASE, "vault.enc")
    with open(vault, "wb") as f:
        f.write(token)
    timings["T4 Encryption (AES)"] = time.perf_counter() - t

    t = time.perf_counter()
    backups = []                                                                   # T6
    for site in ("backup_site_A", "backup_site_B"):
        os.makedirs(os.path.join(CASE, site), exist_ok=True)
        backups.append(shutil.copy(vault, os.path.join(CASE, site, "vault.enc")))
    vault_hash = sha256_file(vault)
    timings["T6 Redundant backups"] = time.perf_counter() - t

    custody.add("insp_patil", "ENCRYPTED", "evidence bundle encrypted, 2 backups made")
    print("Evidence encrypted into vault.enc with 2 off-site backups.")
    return vault, backups, vault_hash


def access(user, permission, custody):                                            # T5
    role = ROLES.get(user)
    allowed = role is not None and permission in PERMISSIONS[role]
    custody.add(user, "ACCESS_GRANTED" if allowed else "ACCESS_DENIED", permission)
    return allowed


def open_vault(vault, backups, vault_hash, user, custody):
    if not access(user, "decrypt", custody):
        return None, "denied by access control"
    for copy in [vault] + backups:                                                 # T6 self-heal
        if os.path.exists(copy) and sha256_file(copy) == vault_hash:
            if copy != vault:
                shutil.copy(copy, vault)
                custody.add(user, "RESTORED", f"vault restored from {os.path.basename(os.path.dirname(copy))}")
            return Fernet(VAULT_KEY).decrypt(open(vault, "rb").read()), "ok"
    return None, "all copies lost"


# =========================================================
# PHASE 3: ANALYSIS
# =========================================================

def analyse(evidence, timings):
    findings = []
    t = time.perf_counter()

    for root, _, files in os.walk(evidence):
        for name in files:
            path = os.path.join(root, name)
            rel = os.path.relpath(path, evidence)
            data = open(path, "rb").read()

            bad = KNOWN_BAD_HASHES.get(hashlib.sha256(data).hexdigest())
            if bad:
                findings.append(f"[HASH MATCH] {rel} is known malware: {bad}")

            real = next((k for m, k in SIGNATURES.items() if data.startswith(m)), None)
            claimed = EXT_TYPES.get(os.path.splitext(name)[1].lower())
            if real and claimed and real != claimed:
                findings.append(f"[SIGNATURE ] {rel} claims {claimed} but is really {real}")

            text = data.decode("latin-1").lower()
            hits = [k for k in KEYWORDS if k in text]
            if hits and not bad:
                findings.append(f"[KEYWORD   ] {rel}: {', '.join(hits)}")

    events = []
    with open(os.path.join(evidence, "logs", "auth.log")) as f:
        for line in f:
            date, clock, user, action, *rest = line.split()
            if user == "user=rahul":
                events.append((f"{date} {clock}", action.split("=")[1], " ".join(rest)))
    events.sort()
    timings["Analysis"] = time.perf_counter() - t
    return findings, events


# =========================================================
# PHASE 4: ATTACKS ON THE EVIDENCE
# =========================================================

def run_attacks(evidence, manifest, vault, backups, vault_hash, custody):
    results = []

    # A1: insider edits an email to remove the incriminating line
    target = os.path.join(evidence, "emails", "mail_01.eml")
    try:
        with open(target, "a") as f:
            f.write("edited")
        blocked = False
    except PermissionError:
        blocked = True
    results.append(("A1 Modify evidence file", "T3 Write blocking", "Integrity",
                     "PREVENTED" if blocked else "NOT PREVENTED"))

    # A2: attacker removes read-only flag and edits anyway -> hash check
    os.chmod(target, stat.S_IREAD | stat.S_IWRITE)
    with open(target, "a") as f:
        f.write("\n(this mail was a joke)\n")
    changed = [rel for rel, h in manifest.items() if sha256_file(os.path.join(evidence, rel)) != h]
    results.append(("A2 Bypass read-only, edit file", "T1 Hashing", "Integrity",
                     f"DETECTED ({', '.join(changed)})" if changed else "NOT DETECTED"))

    # A3: someone deletes the ACCESS_DENIED record from the custody log
    access("clerk_joshi", "decrypt", custody)
    with open(custody.path) as f:
        entries = json.load(f)
    entries = [e for e in entries if e["action"] != "ACCESS_DENIED"]
    with open(custody.path, "w") as f:
        json.dump(entries, f)
    ok, at = custody.verify()
    results.append(("A3 Forge chain-of-custody log", "T2 HMAC custody chain", "Integrity",
                     "NOT DETECTED" if ok else f"DETECTED (broken at entry {at})"))
    with open(custody.path, "w") as f:                     # restore the genuine log
        json.dump(custody.entries, f, indent=1)

    # A4: stolen vault file opened without the key
    try:
        Fernet(Fernet.generate_key()).decrypt(open(vault, "rb").read())
        leaked = True
    except InvalidToken:
        leaked = False
    results.append(("A4 Steal vault, read without key", "T4 Encryption", "Confidentiality",
                     "NOT PREVENTED" if leaked else "PREVENTED (unreadable ciphertext)"))

    # A5: unauthorised staff member asks to decrypt
    data, why = open_vault(vault, backups, vault_hash, "clerk_joshi", custody)
    results.append(("A5 Unauthorised decrypt request", "T5 Access control", "Confidentiality",
                     "PREVENTED" if data is None else "NOT PREVENTED"))

    # A6: ransomware deletes the main vault and corrupts backup A
    os.remove(vault)
    with open(backups[0], "r+b") as f:
        f.write(b"RANSOMWARE")
    data, why = open_vault(vault, backups, vault_hash, "insp_patil", custody)
    results.append(("A6 Delete vault + corrupt backup", "T6 Redundant backups", "Availability",
                     "RECOVERED (from backup B)" if data else f"LOST ({why})"))
    return results


# =========================================================
# PHASE 5: COMPARISON
# =========================================================

CIA = [
    # technique,             C,      I,      A,      strength / limitation
    ("T1 Hashing (SHA-256)", "-", "High", "-", "Detects any change; cannot stop or undo it"),
    ("T2 HMAC custody chain", "-", "High", "-", "Proves who did what, tamper-evident; needs key safety"),
    ("T3 Write blocking", "-", "Medium", "-", "Stops casual edits; admin can remove the flag"),
    ("T4 Encryption (AES)", "High", "Low", "Low", "Stolen data unreadable; lost key = lost evidence"),
    ("T5 Access control", "Medium", "Low", "-", "Limits who can open; useless if account is stolen"),
    ("T6 Redundant backups", "Low", "-", "High", "Survives deletion/ransomware; more copies to guard"),
]


def main():
    timings = {}
    create_crime_scene()

    title("PHASE 1-2: ACQUISITION AND PROTECTION")
    os.makedirs(CASE, exist_ok=True)
    custody = CustodyLog(os.path.join(CASE, "custody_log.json"))
    evidence, manifest = acquire(custody, timings)
    vault, backups, vault_hash = build_vault(evidence, custody, timings)

    t = time.perf_counter()
    access("insp_patil", "analyse", custody)
    timings["T5 Access control"] = time.perf_counter() - t
    t = time.perf_counter()
    custody.verify()
    timings["T2 HMAC custody chain"] = time.perf_counter() - t

    title("PHASE 3: ANALYSIS OF THE CYBER CRIME")
    findings, events = analyse(evidence, timings)
    for f in findings:
        print(f)
    print("\nTimeline of suspect (rahul):")
    for when, action, detail in events:
        print(f"  {when}  {action:12} {detail}")

    title("PHASE 4: ATTACKS ON THE EVIDENCE")
    attacks = run_attacks(evidence, manifest, vault, backups, vault_hash, custody)
    print(f"{'Attack':34}{'Defending technique':24}{'CIA':16}Result")
    print("-" * 100)
    for a, tech, cia, res in attacks:
        print(f"{a:34}{tech:24}{cia:16}{res}")

    title("PHASE 5: COMPARISON OF TECHNIQUES (C / I / A)")
    lines = [f"{'Technique':24}{'Conf.':8}{'Integ.':8}{'Avail.':8}{'Time (ms)':11}Strength / limitation",
             "-" * 110]
    for tech, c, i, a, note in CIA:
        ms = timings.get(tech, 0) * 1000
        lines.append(f"{tech:24}{c:8}{i:8}{a:8}{ms:<11.2f}{note}")
    print("\n".join(lines))

    ok, _ = custody.verify()
    print(f"\nChain of custody intact: {ok}  ({len(custody.entries)} signed entries)")

    report = os.path.join(HERE, "comparison_report.txt")
    with open(report, "w", encoding="utf-8") as f:
        f.write("CASE 2026/041 - Data theft by insider\n\nFINDINGS\n")
        f.write("\n".join(findings) + "\n\nTIMELINE\n")
        f.write("\n".join(f"{w}  {a:12} {d}" for w, a, d in events) + "\n\nATTACK RESULTS\n")
        f.write("\n".join(f"{a:34}{t:24}{c:16}{r}" for a, t, c, r in attacks) + "\n\nCOMPARISON\n")
        f.write("\n".join(lines) + "\n\nCONCLUSION\n"
                "No single technique protects all three of C, I and A. Hashing + HMAC custody give\n"
                "integrity, encryption + access control give confidentiality, and redundant\n"
                "backups give availability, so a forensic lab must combine them.\n")
    print(f"Report saved: {report}")

    # ---------- self-check ----------
    assert any("HASH MATCH" in f for f in findings)
    assert any("holiday.jpg claims JPEG but is really ZIP" in f for f in findings)
    assert all(r.startswith(("PREVENTED", "DETECTED", "RECOVERED")) for *_, r in attacks), attacks
    assert ok
    print("Self-check passed: all attacks were prevented, detected or recovered.")


if __name__ == "__main__":
    main()
