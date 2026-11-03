# Assignment 5: Log Capturing and Event Correlation

## Aim

Write a program for Log Capturing and Event Correlation.

## Theory and Fundamentals

### What is a log?
A **log** is a time-stamped record of something that happened on a system: a login, a blocked packet, a web request, a `sudo` command. Logs are the "CCTV footage" of IT systems and the first thing investigators collect.

| Source | Typical file / protocol | What it shows |
| --- | --- | --- |
| SSH / OS authentication | `/var/log/auth.log` | Failed and accepted logins, `sudo`, `useradd` |
| Web server | Apache/Nginx access log | Client IP, URL, status code, bytes sent |
| Firewall | iptables / UFW kernel messages | Blocked source IP and destination port |
| Network devices | Syslog from routers and switches | Interface changes, ACL hits |

### Syslog
**Syslog** (RFC 5424 / 3164) is the standard way for devices to send log messages to a central server, usually over **UDP port 514** (this lab uses 5514 so no root is needed). A message looks like `<13>Nov 03 01:58:10 srv01 sshd[811]: ...`. The number in `<>` is the **priority** = facility x 8 + severity (13 = user.notice). With rsyslog a Linux server forwards everything with `*.* @collector:5514`.

### Why centralise logs?
- An attacker who gets root can erase local logs; a remote copy survives.
- One place to search and correlate many devices.
- Needed for compliance and for forensic timelines.
- Time must be accurate (**NTP**) or events from different devices cannot be ordered.

### Normalisation
Each product writes a different format. **Normalisation** converts them to one common event shape (time, source, IP, user, type, detail) so that rules can be written once.

### Event correlation
One event alone is usually harmless (one failed login = a typo). **Correlation** links events by time, IP address or user to find a *pattern* that proves an attack. Example: many failed logins -> a success from the same IP -> a root command is a **compromised account**, even though each line looks ordinary.

### SIEM
A **SIEM** (Security Information and Event Management) system collects logs, normalises them, correlates them with rules, raises alerts and keeps a searchable archive. This assignment is a miniature SIEM.

### Attack patterns used in this assignment
- **Port scan:** probing many ports to find open services (firewall shows many blocked ports from one IP).
- **Brute force:** repeated password guesses.
- **SQL injection, XSS, path traversal:** malicious input in web requests.
- **Privilege escalation:** an ordinary account gaining admin powers (`sudo`, new UID 0 user).
- **Data exfiltration:** large unusual downloads of sensitive data.
- **Kill chain:** reconnaissance -> exploitation -> persistence -> data theft.

## How the Code Works

File: `5_LogCorrelation/log_correlator.py` (standard library only). Four stages: **Capture -> Normalise -> Correlate -> Report.**

### 1. Capture
`SyslogHandler` (a `socketserver.BaseRequestHandler`) receives UDP datagrams and appends each line, prefixed with the sender's IP, to `captured.log` under a lock. `start_collector(port)` runs a `ThreadingUDPServer` in a background thread.

```python
for line in data.splitlines():
    f.write(f"{self.client_address[0]} {line}\n")
```
Log files can also be given on the command line instead.

### 2. Normalise: `parse_line(line)`
Regular expressions turn each line into a dictionary with keys `time, source, host, ip, user, type, detail, size, raw`.

| Event type | Recognised from |
| --- | --- |
| `web_request` / `web_attack` | Apache access line; the URL is tested against SQL-injection, XSS and traversal patterns in `WEB_ATTACKS` |
| `login_failed` / `login_success` | `sshd: Failed password ...` / `Accepted ...` |
| `sudo`, `user_added` | `sudo: user : ... COMMAND=` and `useradd: new user: name=` |
| `fw_block` | kernel line with `BLOCK` or `DROP`, `SRC=` and `DPT=` |

The year is fixed (`YEAR = 2026`) because syslog lines have no year.

### 3. Correlate: `correlate(events)`
Events are sorted by time. The helper `recent(ip, kind, now, window)` returns matching events inside a time window. `flagged[ip]` remembers which rules an IP has triggered, and `compromised[user]` remembers accounts taken over.

| Rule | Condition | Severity |
| --- | --- | --- |
| **C1 Port scan** | >= 10 *different* blocked ports from one IP in 60 s | MEDIUM |
| **C2 Brute force** | >= 5 failed SSH logins from one IP in 5 min | HIGH |
| **C3 Account compromised** | a successful login after C2 on that IP, with failures in the last 10 min | CRITICAL |
| **C4 Privilege escalation** | `sudo` or `useradd` by a C3 account within 15 min | CRITICAL |
| **C5 Web attack** | request matching SQLi / XSS / traversal | HIGH |
| **C6 Recon -> attack** | C5 from an IP that already triggered C1 | CRITICAL |
| **C7 Data exfiltration** | download > 5 MB by an IP that has C3 or C6 | CRITICAL |

```python
elif e["type"] == "login_success" and "C2 Brute force" in flagged[ip]:
    if recent(ip, "login_failed", now, timedelta(minutes=10)):
        compromised[e["user"]] = (ip, now)
        raise_alert("C3 Account compromised", "CRITICAL", now, ip, ...)
```
`raise_alert` raises each rule only once per IP, except C4 which appends an alert for each sudo/useradd event (so two C4 alerts appear in the demo). Host events like `sudo` carry no IP, so the code sets `e["ip"] = cip` to link them to the attacker.

### 4. Report: `report(alerts, events)`
Prints event counts per source, the alert list, and a **timeline per attacker IP**; it also writes `correlation_report.txt`.

### Demo data: `demo_logs()`
Three actors: a normal staff member (`192.168.1.15`: one login, two page loads, one typo), a **scanner** (`198.51.100.23`: 12-port scan, SQL injection, path traversal, a 48 MB download) and an **attacker** (`203.0.113.66`: 7 failed logins, success as `admin`, `sudo /bin/bash`, `useradd sysupdate`). `run_demo()` starts the collector on 127.0.0.1:5514 and sends every line as a real UDP syslog message with a `<13>` priority prefix.

## How to Run and Expected Output

```bash
python LP4/CSDF/5_LogCorrelation/log_correlator.py --demo                 # collector + simulated devices + correlation
python LP4/CSDF/5_LogCorrelation/log_correlator.py --listen 5514          # real collector; Ctrl+C to correlate
python LP4/CSDF/5_LogCorrelation/log_correlator.py auth.log access.log firewall.log
```

Real output (trimmed):

```
Captured 30 log lines into ...\5_LogCorrelation\captured.log
Events captured: auth 12, firewall 12, web 6  (total 30)
--- ALERTS (8) ---
[01:59:09] MEDIUM   C1 Port scan             198.51.100.23   10 different ports probed in 60 s
[02:00:00] HIGH     C5 Web attack            198.51.100.23   SQL injection: GET /login.php?user=admin'%20OR%20'1'='1 ...
[02:00:00] CRITICAL C6 Recon -> attack       198.51.100.23   port scan followed by web exploitation
[02:01:32] HIGH     C2 Brute force           203.0.113.66    5 failed SSH logins (users: admin, oracle, root, test)
[02:01:45] CRITICAL C3 Account compromised   203.0.113.66    successful login as 'admin' right after brute force
[02:02:20] CRITICAL C4 Privilege escalation  203.0.113.66    compromised account 'admin' ran sudo: /bin/bash
[02:04:40] CRITICAL C7 Data exfiltration     198.51.100.23   downloaded 48.0 MB from /backup/db_full.sql
Self-check passed: all 7 correlation rules fired, normal user not flagged.
```
(The second C4 alert, for `useradd sysupdate`, is also printed.) Observe that the staff user's one failed login produces no alert; thresholds separate noise from attack.

## Related Concepts and Real-World Tools

- **SIEM / log platforms:** **Splunk**, **ELK / Elastic Stack** (Elasticsearch, Logstash, Kibana), **Wazuh** (open source, host agents + rules), **Graylog**, **IBM QRadar**, **Microsoft Sentinel**.
- **Log shippers/collectors:** rsyslog, syslog-ng, Filebeat, Fluentd, Windows Event Forwarding.
- **Standards:** RFC 5424 (syslog), **Common Event Format (CEF)**, Sigma rules (portable detection rules), MITRE ATT&CK mapping.
- **Fail2ban:** simple log-based blocking.
- **SOAR / SOC:** playbooks that respond automatically; a Security Operations Center watches the SIEM.
- **Windows logs:** Event IDs 4624 (logon), 4625 (failed logon), 4672 (special privileges).
- **Log integrity:** hash and forward logs, restrict access, keep a chain of custody (see Assignment 11).
- **Legal:** IT Act 2000 / CERT-In directions require organisations to keep logs for 180 days and report incidents within 6 hours; Section 43 and 66 cover the offences found.

## Viva Questions

1. **What is event correlation and why is it needed?** Linking separate events by time, IP or user to detect a pattern. A single failed login is harmless; failures, then success, then `sudo` shows a compromise.
2. **What is syslog and which port does it use?** A standard protocol to send logs to a central server, normally UDP 514 (the program uses 5514 to avoid needing root).
3. **Why collect logs centrally?** Attackers delete local logs; a central copy is safe, searchable and gives a single correlated timeline.
4. **What does normalisation mean?** Converting different log formats (SSH, Apache, iptables) into one structure so common rules can be applied.
5. **Explain rule C3.** After C2 (brute force) is flagged for an IP, a successful login from that IP while recent failures exist marks the account as compromised.
6. **How does C6 prove a planned attack?** The same IP first scanned many ports (C1) and later sent web exploit requests (C5), which is a reconnaissance-then-attack sequence.
7. **Why does the program ignore the staff user's single failed login?** Rule C2 needs at least 5 failures in 5 minutes; one typo is below the threshold, so no false alarm.
8. **What is a SIEM and how is this program similar?** A system for collecting, normalising, correlating and alerting on logs. This program does capture, parse, correlate with 7 rules and report.
9. **Why must clocks be synchronised?** Correlation depends on the order and gaps between events from different machines; NTP gives them a common time.
10. **What are the limits of this program?** Fixed year, a few log formats, thresholds are hard-coded, UDP syslog can lose or be spoofed (use TCP/TLS in production), and no persistent database.
