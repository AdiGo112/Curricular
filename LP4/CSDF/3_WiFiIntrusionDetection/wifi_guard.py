# =========================================================
# ASSIGNMENT 3
# Detect and block a Wi-Fi password cracking attempt
# (IEEE 802.11 access point protecting an IP printer)
# =========================================================
#
# SCENARIO (see README.md for the full setup)
#
#   Linux laptop / Raspberry Pi + USB Wi-Fi adapter in AP mode
#   runs  hostapd  (802.11 access point, WPA2-PSK)
#   and   dnsmasq  (DHCP, gives IPs 192.168.4.x)
#   An IP printer is wired to eth0 at 192.168.5.50, so every
#   Wi-Fi -> printer packet is ROUTED through this machine and
#   iptables can filter it (same-BSS traffic would bypass it).
#
#   A person on the road tries password after password.
#   Every wrong WPA2 password makes hostapd log:
#       wlan0: AP-STA-POSSIBLE-PSK-MISMATCH <attacker MAC>
#
# DETECTION RULES
#   R1  Brute force   : >= 5 PSK mismatches from one MAC in 60 s
#   R2  MAC rotation  : >= 8 PSK mismatches from >= 4 different
#                       MACs in 60 s (attacker changes MAC)
#   R3  Deauth attack : >= 3 clients kicked off within 10 s
#                       (attacker forcing re-connects to capture
#                       the WPA handshake for offline cracking)
#   R4  Unknown device: a MAC not in the allowlist gets an IP
#                       (password was cracked) -> printer cut off
#
# RESPONSE (prohibit access)
#   - MAC added to hostapd deny list   (cannot join Wi-Fi)
#   - if it already got an IP, iptables drops its traffic to the
#     printer ports 9100 (RAW), 631 (IPP), 515 (LPD)
#   - commands are only PRINTED unless --enforce is given
#     (needs Linux + root)
#
# =========================================================
# HOW TO RUN
# =========================================================
#
#   python wifi_guard.py --simulate             demo with a generated log
#   python wifi_guard.py /var/log/hostapd.log   analyse a real log
#   ... --allow allowed_macs.txt                registered MACs, one per line (enables R4)
#   sudo python3 wifi_guard.py --follow /var/log/hostapd.log --enforce
#                                               live protection on the AP
#
# =========================================================

import argparse
import os
import re
import subprocess
import sys
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta

PRINTER_IP = "192.168.5.50"
PRINTER_PORTS = (9100, 631, 515)
INTERFACE = "wlan0"

BRUTE_LIMIT, BRUTE_WINDOW = 5, 60
ROTATE_LIMIT, ROTATE_MACS, ROTATE_WINDOW = 8, 4, 60
DEAUTH_LIMIT, DEAUTH_WINDOW = 3, 10

MAC = r"(?P<mac>(?:[0-9a-f]{2}:){5}[0-9a-f]{2})"
EVENTS = [
    ("psk_mismatch", re.compile(rf"AP-STA-POSSIBLE-PSK-MISMATCH {MAC}", re.I)),
    ("connected", re.compile(rf"AP-STA-CONNECTED {MAC}", re.I)),
    ("disconnected", re.compile(rf"AP-STA-DISCONNECTED {MAC}", re.I)),
    ("dhcp", re.compile(rf"DHCPACK\(\w+\) (?P<ip>[\d.]+) {MAC}", re.I)),
]
# hostapd -t prints "1730612345.123456: wlan0: ..."; syslog prints "Nov  3 22:10:01 host hostapd: ..."
EPOCH_TS = re.compile(r"^(\d{9,10}\.\d+):")
SYSLOG_TS = re.compile(r"^([A-Z][a-z]{2}\s+\d+\s[\d:]{8})")


def parse_time(line):
    m = EPOCH_TS.match(line)
    if m:
        return datetime.fromtimestamp(float(m.group(1)))
    m = SYSLOG_TS.match(line)
    if m:
        return datetime.strptime(f"{datetime.now().year} {m.group(1)}", "%Y %b %d %H:%M:%S")
    return datetime.now()


# =========================================================
# DETECTOR
# =========================================================

class WifiGuard:
    def __init__(self, enforce=False, allowlist=None):
        self.enforce = enforce
        self.allowlist = allowlist or set()      # registered staff devices (rule R4)
        self.mismatch = defaultdict(deque)       # mac -> times of wrong passwords
        self.all_mismatch = deque()              # (time, mac) for rotation rule
        self.disconnects = deque()               # (time, mac)
        self.ip_of = {}                          # mac -> ip from DHCP
        self.trusted = set()                     # macs that connected successfully
        self.blocked = set()
        self.alerts = []

    @staticmethod
    def _trim(queue, now, window, key=lambda x: x):
        while queue and now - key(queue[0]) > timedelta(seconds=window):
            queue.popleft()

    def alert(self, when, rule, text):
        msg = f"[{when:%H:%M:%S}] ALERT {rule}: {text}"
        self.alerts.append((rule, text))
        print(msg)

    def block(self, mac, when, reason):
        if mac in self.blocked:
            return
        self.blocked.add(mac)
        cmds = [["hostapd_cli", "-i", INTERFACE, "deny_acl", "ADD_MAC", mac],
                ["hostapd_cli", "-i", INTERFACE, "disassociate", mac]]
        ip = self.ip_of.get(mac)
        if ip:
            for port in PRINTER_PORTS:
                cmds.append(["iptables", "-I", "FORWARD", "-s", ip, "-d", PRINTER_IP,
                             "-p", "tcp", "--dport", str(port), "-j", "DROP"])
        print(f"[{when:%H:%M:%S}] BLOCK {mac} ({reason})" + (f", IP {ip} cut off from printer" if ip else ""))
        for cmd in cmds:
            if self.enforce:
                result = subprocess.run(cmd, capture_output=True, text=True)
                print(f"    ran: {' '.join(cmd)}  -> {'OK' if result.returncode == 0 else result.stderr.strip()}")
            else:
                print(f"    would run: {' '.join(cmd)}")

    def feed(self, line):
        when = parse_time(line)
        for kind, pattern in EVENTS:
            m = pattern.search(line)
            if m:
                getattr(self, "on_" + kind)(when, m.group("mac").lower(), m)
                return

    # ---------- event handlers ----------
    def on_psk_mismatch(self, when, mac, _):
        q = self.mismatch[mac]
        q.append(when)
        self._trim(q, when, BRUTE_WINDOW)
        if len(q) >= BRUTE_LIMIT and mac not in self.blocked:
            self.alert(when, "R1 BRUTE-FORCE", f"{mac} entered a wrong password {len(q)} times in {BRUTE_WINDOW}s")
            self.block(mac, when, "password guessing")

        self.all_mismatch.append((when, mac))
        self._trim(self.all_mismatch, when, ROTATE_WINDOW, key=lambda x: x[0])
        macs = {m for _, m in self.all_mismatch}
        if len(self.all_mismatch) >= ROTATE_LIMIT and len(macs) >= ROTATE_MACS:
            self.alert(when, "R2 MAC-ROTATION", f"{len(self.all_mismatch)} wrong passwords from {len(macs)} "
                                                f"different MACs in {ROTATE_WINDOW}s - attacker is changing MAC")
            for m in macs - self.trusted:
                self.block(m, when, "part of MAC-rotation attack")
            self.all_mismatch.clear()

    def on_connected(self, when, mac, _):
        self.trusted.add(mac)
        self.mismatch.pop(mac, None)            # a correct password resets the counter

    def on_disconnected(self, when, mac, _):
        self.disconnects.append((when, mac))
        self._trim(self.disconnects, when, DEAUTH_WINDOW, key=lambda x: x[0])
        macs = {m for _, m in self.disconnects}
        if len(macs) >= DEAUTH_LIMIT:
            self.alert(when, "R3 DEAUTH-ATTACK", f"{len(macs)} clients dropped within {DEAUTH_WINDOW}s - someone may be "
                                                 "forcing re-connects to capture the WPA handshake")
            self.disconnects.clear()

    def on_dhcp(self, when, mac, m):
        self.ip_of[mac] = m.group("ip")
        if mac in self.blocked:                 # blocked device somehow got an IP: cut printer access
            self.blocked.discard(mac)
            self.block(mac, when, "blocked device received an IP")
        elif self.allowlist and mac not in self.allowlist:
            self.alert(when, "R4 UNKNOWN-DEVICE", f"{mac} joined with the correct password but is not a "
                                                  "registered device - the password may be cracked")
            self.block(mac, when, "unregistered device")


# =========================================================
# SIMULATED SCENARIO
# =========================================================

def simulated_log():
    t0 = datetime(2026, 11, 3, 21, 0, 0).timestamp()
    lines = []

    def log(sec, text):
        lines.append((sec, f"{t0 + sec:.6f}: {text}"))

    office = ["a4:5e:60:11:22:33", "f0:18:98:44:55:66", "3c:22:fb:77:88:99"]
    for i, mac in enumerate(office):                                   # normal staff devices
        log(5 + i, f"wlan0: AP-STA-CONNECTED {mac}")
        log(6 + i, f"dnsmasq-dhcp: DHCPACK(wlan0) 192.168.4.{20 + i} {mac}")
    log(40, f"wlan0: AP-STA-POSSIBLE-PSK-MISMATCH {office[1]}")       # staff typo, then success
    log(48, f"wlan0: AP-STA-CONNECTED {office[1]}")

    # Attacker on the road with a phone: tries a password list
    attacker = "de:ad:be:ef:13:37"
    for k in range(7):
        log(100 + k * 6, f"wlan0: AP-STA-POSSIBLE-PSK-MISMATCH {attacker}")

    # Attacker switches to a laptop with aircrack-ng: deauth to capture the handshake
    for i, mac in enumerate(office):
        log(200 + i, f"wlan0: AP-STA-DISCONNECTED {mac}")
    for i, mac in enumerate(office):
        log(206 + i, f"wlan0: AP-STA-CONNECTED {mac}")

    # Then online guessing with a random MAC each time (MAC rotation)
    for k in range(9):
        log(300 + k * 4, f"wlan0: AP-STA-POSSIBLE-PSK-MISMATCH 02:00:00:aa:{k:02x}:{(k * 37) % 256:02x}")

    # Finally the captured handshake is cracked offline and a new device joins
    log(900, "wlan0: AP-STA-CONNECTED 66:77:88:99:aa:bb")
    log(901, "dnsmasq-dhcp: DHCPACK(wlan0) 192.168.4.66 66:77:88:99:aa:bb")

    return [text for _, text in sorted(lines)], set(office)


def follow(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if line:
                yield line
            else:
                time.sleep(0.5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wi-Fi password-cracking detector for hostapd")
    parser.add_argument("log", nargs="?", help="hostapd / syslog file")
    parser.add_argument("--simulate", action="store_true", help="run the demo scenario")
    parser.add_argument("--follow", action="store_true", help="keep watching the log (live)")
    parser.add_argument("--enforce", action="store_true", help="really run hostapd_cli / iptables (Linux, root)")
    parser.add_argument("--allow", help="file of registered MAC addresses, one per line (enables R4)")
    args = parser.parse_args()

    if args.enforce and (sys.platform != "linux" or os.geteuid() != 0):
        sys.exit("--enforce needs Linux and root (sudo)")

    allow, lines = set(), []
    if args.allow:
        with open(args.allow) as f:
            allow = {line.strip().lower() for line in f if line.strip()}
    if args.simulate:
        lines, allow = simulated_log()

    guard = WifiGuard(enforce=args.enforce, allowlist=allow)
    print(f"Protecting printer {PRINTER_IP} on {INTERFACE}\n")

    if args.simulate:
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "simulated_hostapd.log"), "w") as f:
            f.write("\n".join(lines) + "\n")
        for line in lines:
            guard.feed(line)
    elif args.log and args.follow:
        for line in follow(args.log):
            guard.feed(line)
    elif args.log:
        with open(args.log, encoding="utf-8", errors="replace") as f:
            for line in f:
                guard.feed(line)
    else:
        parser.print_help()
        sys.exit(1)

    print(f"\nSummary: {len(guard.alerts)} alerts, {len(guard.blocked)} devices blocked: {sorted(guard.blocked)}")

    if args.simulate:
        rules = [r for r, _ in guard.alerts]
        assert "de:ad:be:ef:13:37" in guard.blocked
        assert {"R1 BRUTE-FORCE", "R2 MAC-ROTATION", "R3 DEAUTH-ATTACK", "R4 UNKNOWN-DEVICE"} <= set(rules)
        assert "66:77:88:99:aa:bb" in guard.blocked
        assert not guard.blocked & allow
        print("Self-check passed: all four attack patterns detected, intruder cut off from the printer, "
              "staff devices untouched.")
