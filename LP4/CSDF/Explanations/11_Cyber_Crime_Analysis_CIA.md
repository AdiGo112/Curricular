# Assignment 11 (Mini Project): Cyber Crime Analysis and Comparison of Forensic Techniques (CIA)

## Aim

Design a system for the analysis of cyber crime using various cyber forensic techniques and compare each technique with respect to integrity, confidentiality and availability.

## Theory and Fundamentals

### The CIA triad
| Property | Meaning | Threat | Protection |
| --- | --- | --- | --- |
| **Confidentiality** | Only authorised people can read the data | Theft, leak, snooping | Encryption, access control |
| **Integrity** | Data is accurate and unchanged | Tampering, forged logs | Hashing, digital signatures, HMAC, write blocking |
| **Availability** | Data is accessible when needed | Deletion, ransomware, hardware failure | Backups, redundancy |

No single control gives all three; some even weaken one while improving another (e.g. encryption helps confidentiality but a lost key destroys availability). This is the central idea of the assignment.

### Digital forensic process
1. **Identification** of evidence; 2. **Acquisition** (copy without altering); 3. **Preservation** (hash, protect, log); 4. **Analysis**; 5. **Reporting / presentation** in court.
Core principle: *never work on the original; prove the copy is identical and unchanged.*

### Forensic techniques compared in this project
- **Hashing (SHA-256):** a one-way fingerprint. Any change in the file gives a different hash. Detects tampering but cannot prevent or undo it.
- **HMAC:** a hash computed with a secret key, so only the key holder can create a valid value. Used to sign log entries.
- **Chain of custody:** a documented, tamper-evident record of who handled the evidence, when and what they did. Here each entry is signed with HMAC and contains the previous entry's MAC (a hash chain, like a mini blockchain), so deleting or editing an entry breaks the chain.
- **Write blocker:** hardware/software that allows only reading from evidence media. The program imitates it using the read-only file attribute (a real write blocker works at the disk-controller level).
- **Encryption:** the program uses **Fernet** (from the `cryptography` library): AES-128 in CBC mode plus an HMAC-SHA256 authentication tag, with a random IV and a timestamp. Symmetric: the same key encrypts and decrypts.
- **Access control (RBAC):** permissions are given to roles (investigator, viewer), not individuals; "least privilege".
- **Backups / redundancy:** several copies at different locations (3-2-1 rule: 3 copies, 2 media, 1 off-site). Integrity of a backup is checked with its hash.

### Analysis techniques used on the case
- **Known-bad hash matching:** compare file hashes with a list of known malware (like the NSRL / VirusTotal approach).
- **File-signature analysis:** real type vs extension (disguised files).
- **Keyword search:** words such as "confidential", "client", "usb", "delete", "transfer", "password".
- **Timeline analysis:** order of a suspect's actions from log entries.

### Legal points (India)
Evidence is an *electronic record*; admissibility needs a Section 65B certificate (Indian Evidence Act; now Section 63, Bharatiya Sakshya Adhiniyam 2023), which is why hash + chain of custody matter. Relevant offences: IT Act 2000 Section 43 (unauthorised access / data theft), 66, 66C/66D, 72 (breach of confidentiality), 65 (tampering with computer source documents); Section 79A (Examiner of Electronic Evidence).

## How the Code Works

File: `11_CyberCrimeAnalysis/forensic_system.py` (needs `cryptography`). `main()` runs five phases for a made-up **insider data theft** case: employee Rahul is suspected of copying the client database to a USB drive and mailing it out.

### Phase 0: crime scene
`create_crime_scene()` writes `crime_scene/` with: two e-mails (one incriminating), `auth.log` (login, USB insert, file copy, rename `clients.zip` to `holiday.jpg`, logout; plus a different user's login), `clients.csv`, `holiday.jpg` (actually a ZIP), and `svchost_update.exe` containing the sample "keylogger" bytes.

### Phase 1-2: acquisition and protection
`acquire()` copies the scene to `case_2026_041/evidence`, then:
- **T1:** SHA-256 of each file into `manifest.json`.
- **T3:** every file `os.chmod(..., S_IREAD)` (read-only).
- Custody entries `ACQUIRED`, `HASHED`.

`build_vault()`:
- **T4:** zips the evidence and encrypts it with Fernet into `vault.enc`.
- **T6:** copies the vault to `backup_site_A` and `backup_site_B`; stores the vault hash.

`access(user, permission, custody)` is **T5**: looks up the role in `ROLES` / `PERMISSIONS` and logs `ACCESS_GRANTED` or `ACCESS_DENIED`.

### T2: `CustodyLog`
```python
prev = self.entries[-1]["mac"] if self.entries else "0" * 64
entry = {"time": ..., "who": who, "action": action, "detail": detail, "prev": prev}
entry["mac"] = self._mac(entry)       # HMAC-SHA256 with CUSTODY_KEY
```
`verify()` re-reads the file and checks each entry's `prev` link and its HMAC. Because links alone cannot reveal entries removed from the **end** of the log, it also compares the last MAC with the head kept in memory (the "supervisor's copy").

### Phase 3: analysis (`analyse()`)
For each evidence file: SHA-256 against `KNOWN_BAD_HASHES` (**hash match**), leading bytes against `SIGNATURES` versus the extension (**signature**), a keyword scan (**keyword**); then builds the suspect's **timeline** from `auth.log` lines with `user=rahul`.

### Phase 4: attacks on the evidence (`run_attacks()`)
| Attack | Defence tested | Method of defence | Outcome |
| --- | --- | --- | --- |
| A1 Modify an evidence file | T3 write blocking | Write raises `PermissionError` | PREVENTED |
| A2 Remove read-only flag, edit | T1 hashing | Recomputed hash differs from manifest | DETECTED |
| A3 Delete the `ACCESS_DENIED` record from the log | T2 HMAC chain | Chain / head check fails | DETECTED |
| A4 Steal vault, open with a wrong key | T4 encryption | Fernet raises `InvalidToken` | PREVENTED |
| A5 Unauthorised user asks to decrypt | T5 access control | Role "viewer" lacks `decrypt` | PREVENTED |
| A6 Ransomware deletes vault, corrupts backup A | T6 backups | `open_vault` finds a copy whose hash matches and restores it | RECOVERED (from backup B) |

### Phase 5: comparison (`CIA` table)
```python
("T1 Hashing (SHA-256)", "-",    "High", "-",    "Detects any change; cannot stop or undo it"),
("T4 Encryption (AES)",  "High", "Low",  "Low",  "Stolen data unreadable; lost key = lost evidence"),
("T6 Redundant backups", "Low",  "-",    "High", "Survives deletion/ransomware; more copies to guard"),
```
The ratings (High / Medium / Low / -) are the author's qualitative judgement, entered in the table by hand. The **time cost** column is measured with `time.perf_counter()` in the run. The result is written to `comparison_report.txt` with the conclusion that C, I and A need a combination of techniques. Keys (`CUSTODY_KEY`, `VAULT_KEY`) are generated in memory for the demo; a real lab would use a key vault / HSM.

## How to Run and Expected Output

```bash
pip install cryptography
python LP4/CSDF/11_CyberCrimeAnalysis/forensic_system.py
```
No arguments; it recreates `crime_scene/` and `case_2026_041/` each time (it removes the old case folder, handling read-only files).

Real output (trimmed):

```
[SIGNATURE ] docs\holiday.jpg claims JPEG but is really ZIP
[KEYWORD   ] emails\mail_01.eml: confidential, client, delete, transfer
[HASH MATCH] tools\svchost_update.exe is known malware: Keylogger (in known-bad hash list)
Timeline of suspect (rahul):
  2026-10-20 22:12:40  USB_INSERT   device=SanDisk_32GB
  2026-10-20 22:14:03  FILE_COPY    file=clients.csv dest=E:\
  2026-10-20 22:29:57  FILE_RENAME  file=clients.zip new=holiday.jpg
A1 Modify evidence file           T3 Write blocking       Integrity       PREVENTED
A2 Bypass read-only, edit file    T1 Hashing              Integrity       DETECTED (emails\mail_01.eml)
A3 Forge chain-of-custody log     T2 HMAC custody chain   Integrity       DETECTED (broken at entry 4)
A6 Delete vault + corrupt backup  T6 Redundant backups    Availability    RECOVERED (from backup B)
T4 Encryption (AES)     High    Low     Low     48.25  Stolen data unreadable; lost key = lost evidence
Chain of custody intact: True  (8 signed entries)
Self-check passed: all attacks were prevented, detected or recovered.
```
The millisecond figures change on every run. The story from the evidence: Rahul logged in at night, inserted a USB, copied the client list, disguised it as a "photo", and e-mailed it to an outside buyer.

## Related Concepts and Real-World Tools

- **Forensic suites:** Autopsy, FTK, EnCase, X-Ways; **FTK Imager / `dd` / Guymager** for imaging.
- **Hardware write blockers:** Tableau, WiebeTech; **hash tools:** `sha256sum`, HashMyFiles.
- **Encryption:** AES-256, BitLocker, VeraCrypt, GPG; **digital signatures / PKI** (RSA, ECDSA) give integrity *and* non-repudiation, which HMAC cannot (the key is shared).
- **Trusted timestamps, blockchain-style audit logs**, WORM storage.
- **Access control models:** DAC, MAC, **RBAC**, ABAC; **IAM** and multi-factor authentication.
- **Backup:** 3-2-1 rule, immutable backups, off-site / cloud, regular restore tests.
- **Standards:** ISO/IEC 27037 (evidence handling), 27041-43, NIST SP 800-86, ACPO guidelines, **CERT-In** incident reporting.
- **Other CIA-related threats:** DDoS (availability), man-in-the-middle (confidentiality/integrity).
- **Legal:** IT Act 2000 Sections 43, 65, 66, 66C, 66D, 72, 79A; Section 65B Indian Evidence Act / Section 63 BSA 2023.

## Viva Questions

1. **Explain the CIA triad.** Confidentiality: only authorised people read data. Integrity: data is unaltered and trustworthy. Availability: data is accessible when needed.
2. **Which technique protects which property in your system?** Hashing, HMAC custody log and write blocking protect integrity; encryption and access control protect confidentiality; redundant backups protect availability.
3. **What is chain of custody and why does it matter?** A record of who handled the evidence, when and why. Without an unbroken chain a court may reject the evidence.
4. **How does your custody log detect tampering?** Each entry stores the previous entry's HMAC and its own HMAC computed with a secret key. Editing or deleting an entry breaks a link or a MAC, and a deleted last entry is caught by comparing with the head MAC.
5. **Hash vs HMAC vs digital signature?** A hash is a keyless fingerprint; HMAC adds a shared secret key so only key holders can create it; a digital signature uses a private/public key pair and also gives non-repudiation.
6. **Why is hashing alone not enough for integrity?** It detects change but cannot prevent it, and an attacker who can edit the file may also recompute and replace the hash unless the hash is stored securely or signed.
7. **What is a write blocker and how did you simulate it?** A device or software allowing read-only access to evidence. The program sets the read-only attribute; it can be removed by an administrator, which is why attack A2 is caught by hashing instead.
8. **Why does encryption rate "Low" for availability?** If the key is lost the evidence can never be decrypted, so access is lost even though the data is safe.
9. **How did the system survive the ransomware attack A6?** Two backup copies were stored with the vault's SHA-256; `open_vault` found a copy whose hash matched (backup B) and restored the vault from it.
10. **Why do we need a combination of techniques?** Each technique covers only one or two of C, I, A and has limitations (e.g. access control fails if an account is stolen), so a forensic lab layers several controls.
