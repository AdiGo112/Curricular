# =========================================================
# ASSIGNMENT 6 - Mini IDS (how Snort works, in ~150 lines)
# =========================================================
#
# Reads a .pcap file, decodes Ethernet / IPv4 / TCP / UDP / ICMP,
# and checks every packet against the SAME local.rules file
# that is given to Snort. Supported rule options:
#   msg, sid, content (+ nocase), pcre, flags, itype,
#   detection_filter: track by_src, count N, seconds S
#
# Like Snort's console output, every match prints:
#   [**] [1:sid:rev] message [**]  src:port -> dst:port
#
# RUN:  python make_test_traffic.py      (creates test_traffic.pcap)
#       python mini_ids.py               (checks it with local.rules)
#       python mini_ids.py capture.pcap  (your own Wireshark capture,
#                                         save as "Wireshark/tcpdump - pcap")
#
# =========================================================

import ipaddress
import os
import re
import struct
import sys
from collections import Counter, defaultdict, deque

HOME_NET = ipaddress.ip_network("192.168.1.0/24")
PROTO = {1: "icmp", 6: "tcp", 17: "udp"}
FLAG_BITS = {"F": 0x01, "S": 0x02, "R": 0x04, "P": 0x08, "A": 0x10, "U": 0x20}


# =========================================================
# RULE PARSER
# =========================================================

RULE_RE = re.compile(r"^(alert|log|pass)\s+(\w+)\s+(\S+)\s+(\S+)\s+->\s+(\S+)\s+(\S+)\s+\((.*)\)\s*$")


def parse_rules(path):
    rules = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = RULE_RE.match(line.strip())
            if not m:
                continue
            action, proto, src, sport, dst, dport, opts = m.groups()
            rule = {"proto": proto, "src": src, "sport": sport, "dst": dst, "dport": dport,
                    "contents": [], "rev": 1}
            for opt in re.findall(r'(\w+)(?::\s*("(?:[^"\\]|\\.)*"|[^;]*))?;', opts):
                key, value = opt[0], opt[1].strip().strip('"')
                if key == "content":
                    rule["contents"].append([value.encode(), False])
                elif key == "nocase":
                    rule["contents"][-1][1] = True
                elif key == "pcre":
                    body, flags = value[1:].rsplit("/", 1)
                    rule["pcre"] = re.compile(body.encode(), re.I if "i" in flags else 0)
                elif key == "detection_filter":
                    rule["count"] = int(re.search(r"count\s+(\d+)", value).group(1))
                    rule["seconds"] = int(re.search(r"seconds\s+(\d+)", value).group(1))
                elif key in ("msg", "flags"):
                    rule[key] = value
                elif key in ("sid", "rev", "itype"):
                    rule[key] = int(value)
            rules.append(rule)
    return rules


def addr_ok(spec, ip):
    if spec == "any":
        return True
    if spec == "$HOME_NET":
        return ipaddress.ip_address(ip) in HOME_NET
    return ip == spec


def port_ok(spec, port):
    return spec == "any" or (port is not None and int(spec) == port)


# =========================================================
# PCAP + PACKET DECODER
# =========================================================

def read_pcap(path):
    with open(path, "rb") as f:
        data = f.read()
    magic = struct.unpack("<I", data[:4])[0]
    endian = "<" if magic in (0xA1B2C3D4, 0xA1B23C4D) else ">"
    if struct.unpack(endian + "I", data[20:24])[0] != 1:
        sys.exit("Only Ethernet captures are supported (save as pcap, not pcapng)")
    pos = 24
    while pos + 16 <= len(data):
        sec, usec, incl, _ = struct.unpack(endian + "IIII", data[pos:pos + 16])
        yield sec + usec / 1e6, data[pos + 16:pos + 16 + incl]
        pos += 16 + incl


def decode(frame):
    if len(frame) < 34 or frame[12:14] != b"\x08\x00":
        return None                                           # not IPv4
    ip = frame[14:]
    ihl = (ip[0] & 0x0F) * 4
    proto = ip[9]
    pkt = {"proto": PROTO.get(proto, str(proto)),
           "src": ".".join(map(str, ip[12:16])), "dst": ".".join(map(str, ip[16:20])),
           "sport": None, "dport": None, "flags": 0, "payload": b"", "itype": None}
    l4 = ip[ihl:]
    if proto == 6:
        pkt["sport"], pkt["dport"] = struct.unpack("!HH", l4[:4])
        pkt["flags"] = l4[13]
        pkt["payload"] = l4[(l4[12] >> 4) * 4:]
    elif proto == 17:
        pkt["sport"], pkt["dport"] = struct.unpack("!HH", l4[:4])
        pkt["payload"] = l4[8:]
    elif proto == 1:
        pkt["itype"] = l4[0]
    return pkt


# =========================================================
# DETECTION ENGINE
# =========================================================

def matches(rule, pkt):
    if rule["proto"] != pkt["proto"]:
        return False
    if not (addr_ok(rule["src"], pkt["src"]) and addr_ok(rule["dst"], pkt["dst"])
            and port_ok(rule["sport"], pkt["sport"]) and port_ok(rule["dport"], pkt["dport"])):
        return False
    if "itype" in rule and rule["itype"] != pkt["itype"]:
        return False
    if "flags" in rule:
        wanted = sum(FLAG_BITS[c] for c in rule["flags"] if c in FLAG_BITS)
        if pkt["flags"] & 0x3F != wanted:                     # exact flag set, like Snort's flags:S
            return False
    for content, nocase in rule["contents"]:
        hay = pkt["payload"].lower() if nocase else pkt["payload"]
        if (content.lower() if nocase else content) not in hay:
            return False
    if "pcre" in rule and not rule["pcre"].search(pkt["payload"]):
        return False
    return True


def run(pcap, rules):
    history = defaultdict(deque)               # (sid, src) -> times, for detection_filter
    alerts = []
    total = 0
    for ts, frame in read_pcap(pcap):
        pkt = decode(frame)
        if not pkt:
            continue
        total += 1
        for rule in rules:
            if not matches(rule, pkt):
                continue
            if "count" in rule:                # only alert once the rate threshold is crossed
                q = history[(rule["sid"], pkt["src"])]
                q.append(ts)
                while q and ts - q[0] > rule["seconds"]:
                    q.popleft()
                if len(q) < rule["count"]:
                    continue
            sport = f":{pkt['sport']}" if pkt["sport"] is not None else ""
            dport = f":{pkt['dport']}" if pkt["dport"] is not None else ""
            print(f"[**] [1:{rule['sid']}:{rule['rev']}] {rule['msg']} [**]  "
                  f"{{{pkt['proto'].upper()}}} {pkt['src']}{sport} -> {pkt['dst']}{dport}")
            alerts.append(rule["sid"])
    return total, alerts


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    pcap = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "test_traffic.pcap")
    rules = parse_rules(os.path.join(here, "local.rules"))
    print(f"Loaded {len(rules)} rules from local.rules; reading {os.path.basename(pcap)}\n")

    total, alerts = run(pcap, rules)
    counts = Counter(alerts)
    print(f"\n{total} packets analysed, {len(alerts)} alerts")
    for rule in rules:
        print(f"  sid {rule['sid']}  {counts.get(rule['sid'], 0):3}  {rule['msg']}")

    if len(sys.argv) == 1:                     # self-check on the generated lab traffic
        # SYN scan: 15 ports, alerts from the 10th SYN on = 6; Telnet: scanned port 23 + real attempt = 2
        expected = {1000001: 5, 1000002: 6, 1000003: 1, 1000004: 1, 1000005: 1, 1000006: 1, 1000007: 1, 1000008: 2}
        assert dict(counts) == expected, dict(counts)
        print("\nSelf-check passed: every rule fired the expected number of times, normal traffic raised no alert.")
