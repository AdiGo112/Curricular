# =========================================================
# ASSIGNMENT 5
# Log Capturing and Event Correlation
# =========================================================
#
# 1. CAPTURE  - a syslog collector listens on UDP port 5514.
#               Routers, firewalls and Linux servers can send
#               their logs to it (rsyslog: *.* @collector:5514).
#               Every line is stored with the sender's address.
#               Log files can also be read directly.
#
# 2. NORMALISE - each line from SSH (auth.log), the web server
#               (Apache access log) and the firewall (iptables)
#               becomes one event: time, source, IP, user, type.
#
# 3. CORRELATE - single events look harmless; the SEQUENCE
#               reveals the attack. Rules (per attacker IP / user):
#   C1 Port scan            >= 10 blocked ports from one IP in 60 s
#   C2 Brute force          >= 5 failed logins from one IP in 5 min
#   C3 Account compromised  C2 followed by a successful login from
#                           the same IP within 10 min
#   C4 Privilege escalation compromised user runs sudo / adds user
#                           within 15 min of C3
#   C5 Web attack           SQL injection / XSS / path traversal
#                           requests from an IP
#   C6 Recon -> attack      C1 and C5 from the same IP (planned attack)
#   C7 Data exfiltration    large download (> 5 MB) by an IP that
#                           already triggered C3 or C6
#
# 4. REPORT   - alerts plus a full timeline per attacker IP.
#
# =========================================================
# HOW TO RUN
# =========================================================
#
#   python log_correlator.py --demo
#         starts the collector, simulated devices send logs over
#         UDP, then the captured logs are correlated
#
#   python log_correlator.py --listen 5514
#         run as a real collector (Ctrl+C to stop and correlate)
#
#   python log_correlator.py auth.log access.log firewall.log
#         correlate existing log files
#
# =========================================================

import argparse
import os
import re
import socket
import socketserver
import sys
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
CAPTURE_FILE = os.path.join(HERE, "captured.log")
YEAR = 2026

WEB_ATTACKS = [
    ("SQL injection", re.compile(r"('|%27)(\s|%20|\+)*(or|and|union)\b|union(\s|%20|\+)+select|sleep\(|--\s*$", re.I)),
    ("XSS", re.compile(r"<script|%3Cscript|javascript:|onerror=", re.I)),
    ("Path traversal", re.compile(r"\.\./|%2e%2e%2f|/etc/passwd", re.I)),
]


# =========================================================
# 1. CAPTURE (UDP syslog collector)
# =========================================================

class SyslogHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].decode("utf-8", errors="replace").strip()
        with self.server.lock, open(CAPTURE_FILE, "a", encoding="utf-8") as f:
            for line in data.splitlines():
                f.write(f"{self.client_address[0]} {line}\n")


def start_collector(port, host="0.0.0.0"):
    server = socketserver.ThreadingUDPServer((host, port), SyslogHandler)
    server.lock = threading.Lock()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


# =========================================================
# 2. NORMALISE
# =========================================================

SYSLOG_HEAD = re.compile(r"^(?:(?P<sender>[\d.]+) )?(?:<\d+>)?(?P<ts>[A-Z][a-z]{2}\s+\d+\s[\d:]{8}) (?P<host>\S+) (?P<msg>.*)$")
APACHE = re.compile(r'(?P<ip>[\d.]+) \S+ \S+ \[(?P<ts>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+)[^"]*" '
                    r'(?P<status>\d{3}) (?P<size>\d+|-)')


def parse_line(line):
    line = line.strip()
    # Apache line may arrive via syslog: "<sender> <ts> host apache: <access log line>"
    m = SYSLOG_HEAD.match(line)
    msg, host, when = line, "", None
    if m:
        msg, host = m.group("msg"), m.group("host")
        when = datetime.strptime(f"{YEAR} {m.group('ts')}", "%Y %b %d %H:%M:%S")

    a = APACHE.search(msg)
    if a:
        t = datetime.strptime(a.group("ts").split()[0], "%d/%b/%Y:%H:%M:%S")
        size = 0 if a.group("size") == "-" else int(a.group("size"))
        attack = next((name for name, rx in WEB_ATTACKS if rx.search(a.group("path"))), None)
        return {"time": t, "source": "web", "host": host, "ip": a.group("ip"), "user": "",
                "type": "web_attack" if attack else "web_request", "detail": attack or a.group("path"),
                "size": size, "status": int(a.group("status")), "raw": msg}
    if when is None:
        return None

    patterns = [
        ("login_failed", r"sshd\[\d+\]: Failed password for (?:invalid user )?(?P<user>\S+) from (?P<ip>[\d.]+)"),
        ("login_success", r"sshd\[\d+\]: Accepted \w+ for (?P<user>\S+) from (?P<ip>[\d.]+)"),
        ("sudo", r"sudo:\s+(?P<user>\S+) : .*COMMAND=(?P<detail>.*)"),
        ("user_added", r"useradd\[\d+\]: new user: name=(?P<detail>[^,]+)"),
        ("fw_block", r"kernel: .*(?:BLOCK|DROP).*SRC=(?P<ip>[\d.]+) .*DPT=(?P<detail>\d+)"),
    ]
    for kind, rx in patterns:
        m2 = re.search(rx, msg)
        if m2:
            g = m2.groupdict()
            return {"time": when, "source": "firewall" if kind == "fw_block" else "auth", "host": host,
                    "ip": g.get("ip", ""), "user": g.get("user", ""), "type": kind,
                    "detail": (g.get("detail") or "").strip(), "size": 0, "raw": msg}
    return None


# =========================================================
# 3. CORRELATE
# =========================================================

def correlate(events):
    events = sorted(events, key=lambda e: e["time"])
    alerts = []
    flagged = defaultdict(set)                    # ip -> rules triggered
    compromised = {}                              # user -> (ip, time)

    def raise_alert(rule, severity, when, ip, text):
        if rule in flagged[ip]:
            return
        flagged[ip].add(rule)
        alerts.append({"rule": rule, "severity": severity, "time": when, "ip": ip, "text": text})

    def recent(ip, kind, now, window):
        return [e for e in events if e["ip"] == ip and e["type"] == kind
                and timedelta(0) <= now - e["time"] <= window]

    for e in events:
        ip, now = e["ip"], e["time"]
        if e["type"] == "fw_block":
            ports = {x["detail"] for x in recent(ip, "fw_block", now, timedelta(seconds=60))}
            if len(ports) >= 10:
                raise_alert("C1 Port scan", "MEDIUM", now, ip, f"{len(ports)} different ports probed in 60 s")

        elif e["type"] == "login_failed":
            fails = recent(ip, "login_failed", now, timedelta(minutes=5))
            if len(fails) >= 5:
                users = sorted({x["user"] for x in fails})
                raise_alert("C2 Brute force", "HIGH", now, ip, f"{len(fails)} failed SSH logins (users: {', '.join(users)})")

        elif e["type"] == "login_success" and "C2 Brute force" in flagged[ip]:
            if recent(ip, "login_failed", now, timedelta(minutes=10)):
                compromised[e["user"]] = (ip, now)
                raise_alert("C3 Account compromised", "CRITICAL", now, ip,
                            f"successful login as '{e['user']}' right after brute force")

        elif e["type"] in ("sudo", "user_added"):
            for user, (cip, ctime) in compromised.items():
                actor = e["user"] or user
                if actor == user and now - ctime <= timedelta(minutes=15):
                    what = f"ran sudo: {e['detail']}" if e["type"] == "sudo" else f"created user '{e['detail']}'"
                    e["ip"] = cip                                 # link host event to attacker IP
                    alerts.append({"rule": "C4 Privilege escalation", "severity": "CRITICAL", "time": now,
                                   "ip": cip, "text": f"compromised account '{user}' {what}"})
                    flagged[cip].add("C4 Privilege escalation")

        elif e["type"] == "web_attack":
            raise_alert("C5 Web attack", "HIGH", now, ip, f"{e['detail']}: {e['raw'].split('\"')[1][:70]}")
            if "C1 Port scan" in flagged[ip]:
                raise_alert("C6 Recon -> attack", "CRITICAL", now, ip, "port scan followed by web exploitation")

        if e["source"] == "web" and e["size"] > 5_000_000:
            if flagged[ip] & {"C3 Account compromised", "C6 Recon -> attack"}:
                raise_alert("C7 Data exfiltration", "CRITICAL", now, ip,
                            f"downloaded {e['size'] / 1e6:.1f} MB from {e['detail']}")
    return alerts, events


# =========================================================
# 4. REPORT
# =========================================================

def report(alerts, events):
    lines = ["=" * 78, " EVENT CORRELATION REPORT", "=" * 78]
    by_source = defaultdict(int)
    for e in events:
        by_source[e["source"]] += 1
    lines.append("Events captured: " + ", ".join(f"{k} {v}" for k, v in sorted(by_source.items()))
                 + f"  (total {len(events)})")

    lines.append(f"\n--- ALERTS ({len(alerts)}) ---")
    for a in alerts:
        lines.append(f"[{a['time']:%H:%M:%S}] {a['severity']:8} {a['rule']:24} {a['ip']:15} {a['text']}")

    for ip in sorted({a["ip"] for a in alerts}):
        lines.append(f"\n--- TIMELINE for attacker {ip} ---")
        for e in events:
            if e["ip"] == ip and e["type"] not in ("web_request",) or (e["ip"] == ip and e["size"] > 5_000_000):
                lines.append(f"  {e['time']:%H:%M:%S}  {e['source']:8} {e['type']:14} {e['user']:7} {e['detail'][:60]}")
    return "\n".join(lines)


# =========================================================
# DEMO: simulated devices sending logs over UDP
# =========================================================

def demo_logs():
    attacker, scanner, staff = "203.0.113.66", "198.51.100.23", "192.168.1.15"
    t = datetime(YEAR, 11, 3, 1, 58, 0)
    out = []

    def sys_(sec, host, msg):
        out.append((sec, f"{(t + timedelta(seconds=sec)):%b %d %H:%M:%S} {host} {msg}"))

    def web(sec, ip, path, status=200, size=1500):
        ts = (t + timedelta(seconds=sec)).strftime("%d/%b/%Y:%H:%M:%S +0530")
        out.append((sec, f"{(t + timedelta(seconds=sec)):%b %d %H:%M:%S} web01 apache: "
                         f'{ip} - - [{ts}] "GET {path} HTTP/1.1" {status} {size}'))

    # normal activity
    sys_(10, "srv01", f"sshd[811]: Accepted password for aditya from {staff} port 50122 ssh2")
    web(20, staff, "/index.php")
    web(25, staff, "/notices.php")
    sys_(30, "srv01", f"sshd[812]: Failed password for aditya from {staff} port 50123 ssh2")   # 1 typo: normal

    # scanner: port scan then SQL injection / traversal
    for i, port in enumerate((21, 22, 23, 25, 53, 80, 110, 139, 143, 445, 3306, 3389)):
        sys_(60 + i, "fw01", f"kernel: [UFW BLOCK] IN=eth0 OUT= SRC={scanner} DST=10.0.0.5 PROTO=TCP SPT=4{i}211 DPT={port}")
    web(120, scanner, "/login.php?user=admin'%20OR%20'1'='1", 200, 900)
    web(125, scanner, "/products.php?id=1%20UNION%20SELECT%20username,password%20FROM%20users", 200, 4200)
    web(130, scanner, "/download.php?file=../../../../etc/passwd", 200, 2100)
    web(400, scanner, "/backup/db_full.sql", 200, 48_000_000)

    # attacker: SSH brute force, success, privilege escalation
    for i, user in enumerate(["root", "admin", "test", "oracle", "admin", "admin", "admin"]):
        sys_(200 + i * 3, "srv01", f"sshd[9{i}0]: Failed password for {'invalid user ' if user in ('test', 'oracle') else ''}"
                                   f"{user} from {attacker} port 5{i}100 ssh2")
    sys_(225, "srv01", f"sshd[999]: Accepted password for admin from {attacker} port 51999 ssh2")
    sys_(260, "srv01", "sudo:    admin : TTY=pts/1 ; PWD=/home/admin ; USER=root ; COMMAND=/bin/bash")
    sys_(290, "srv01", "useradd[1203]: new user: name=sysupdate, UID=0, GID=0, home=/root")
    return [line for _, line in sorted(out)]


def run_demo(port):
    if os.path.exists(CAPTURE_FILE):
        os.remove(CAPTURE_FILE)
    server = start_collector(port, "127.0.0.1")       # demo: this machine only
    print(f"Collector listening on UDP {port}; simulated devices are sending logs...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for line in demo_logs():
        sock.sendto(f"<13>{line}".encode(), ("127.0.0.1", port))   # <13> = syslog priority (user.notice)
        time.sleep(0.005)
    time.sleep(0.5)
    server.shutdown()
    with open(CAPTURE_FILE, encoding="utf-8") as f:
        captured = f.read().splitlines()
    print(f"Captured {len(captured)} log lines into {CAPTURE_FILE}\n")
    return captured


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log capture and event correlation")
    parser.add_argument("files", nargs="*", help="log files to correlate")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--listen", type=int, metavar="PORT", help="run as a UDP syslog collector")
    args = parser.parse_args()

    if args.demo:
        raw = run_demo(5514)
    elif args.listen:
        start_collector(args.listen)
        print(f"Collecting syslog on UDP {args.listen} into {CAPTURE_FILE}. Press Ctrl+C to stop and correlate.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        with open(CAPTURE_FILE, encoding="utf-8") as f:
            raw = f.read().splitlines()
    elif args.files:
        raw = []
        for path in args.files:
            with open(path, encoding="utf-8", errors="replace") as f:
                raw += f.read().splitlines()
    else:
        parser.print_help()
        sys.exit(1)

    events = [e for e in map(parse_line, raw) if e]
    alerts, events = correlate(events)
    text = report(alerts, events)
    print(text)
    with open(os.path.join(HERE, "correlation_report.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")

    if args.demo:
        rules = {a["rule"] for a in alerts}
        assert rules == {"C1 Port scan", "C2 Brute force", "C3 Account compromised", "C4 Privilege escalation",
                         "C5 Web attack", "C6 Recon -> attack", "C7 Data exfiltration"}, rules
        assert not any(a["ip"] == "192.168.1.15" for a in alerts), "normal user must not be flagged"
        print("\nSelf-check passed: all 7 correlation rules fired, normal user not flagged.")
