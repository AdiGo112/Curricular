# =========================================================
# ASSIGNMENT 6 - helper
# Generate a real .pcap file with normal + attack traffic
# =========================================================
#
# The packets are built byte by byte (Ethernet / IPv4 / TCP /
# UDP / ICMP with correct checksums), so the file opens in
# Wireshark and can be read by Snort:
#
#     wireshark test_traffic.pcap
#     snort -r test_traffic.pcap -c /etc/snort/snort.conf -A console
#
# Traffic inside (attacker 10.0.0.66 -> lab network 192.168.1.0/24):
#   1. Normal DNS query + HTTP page visit from a staff PC
#   2. ICMP ping sweep of 5 hosts
#   3. SYN port scan of 15 ports on the web server
#   4. Nmap XMAS scan packet
#   5. HTTP requests with SQL injection and path traversal
#   6. FTP login with a cleartext password
#   7. Telnet connection attempt
#
# RUN:  python make_test_traffic.py
#
# =========================================================

import os
import struct

STAFF, ATTACKER, WEB, FTP = "192.168.1.15", "10.0.0.66", "192.168.1.10", "192.168.1.20"
MAC = {STAFF: "00:1a:2b:00:00:15", ATTACKER: "de:ad:be:ef:00:66", WEB: "00:1a:2b:00:00:10",
       FTP: "00:1a:2b:00:00:20", "192.168.1.1": "00:1a:2b:00:00:01"}
FIN, SYN, RST, PSH, ACK, URG = 0x01, 0x02, 0x04, 0x08, 0x10, 0x20


def checksum(data):
    if len(data) % 2:
        data += b"\x00"
    total = sum(struct.unpack(f"!{len(data) // 2}H", data))
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return ~total & 0xFFFF


def ip_bytes(ip):
    return bytes(int(x) for x in ip.split("."))


def ethernet(src, dst, payload):
    mac = lambda ip: bytes.fromhex(MAC.get(ip, "00:1a:2b:ff:ff:ff").replace(":", ""))
    return mac(dst) + mac(src) + b"\x08\x00" + payload


def ipv4(src, dst, proto, payload, ident=[1000]):
    ident[0] += 1
    header = struct.pack("!BBHHHBBH4s4s", 0x45, 0, 20 + len(payload), ident[0], 0x4000, 64, proto, 0,
                         ip_bytes(src), ip_bytes(dst))
    header = header[:10] + struct.pack("!H", checksum(header)) + header[12:]
    return ethernet(src, dst, header + payload)


def tcp(src, dst, sport, dport, flags, seq=0, ack=0, data=b""):
    header = struct.pack("!HHIIBBHHH", sport, dport, seq, ack, 5 << 4, flags, 64240, 0, 0)
    pseudo = ip_bytes(src) + ip_bytes(dst) + struct.pack("!BBH", 0, 6, len(header) + len(data))
    csum = checksum(pseudo + header + data)
    header = header[:16] + struct.pack("!H", csum) + header[18:]
    return ipv4(src, dst, 6, header + data)


def udp(src, dst, sport, dport, data):
    header = struct.pack("!HHHH", sport, dport, 8 + len(data), 0)
    pseudo = ip_bytes(src) + ip_bytes(dst) + struct.pack("!BBH", 0, 17, 8 + len(data))
    header = header[:6] + struct.pack("!H", checksum(pseudo + header + data))
    return ipv4(src, dst, 17, header + data)


def icmp_echo(src, dst, seq):
    body = struct.pack("!BBHHH", 8, 0, 0, 0x4242, seq) + b"abcdefghijklmnopqrstuvwabcdefghi"
    body = body[:2] + struct.pack("!H", checksum(body)) + body[4:]
    return ipv4(src, dst, 1, body)


class Session:
    """A TCP connection with a proper 3-way handshake so Wireshark can follow the stream."""

    def __init__(self, packets, client, server, cport, sport):
        self.p, self.c, self.s, self.cp, self.sp = packets, client, server, cport, sport
        self.cseq, self.sseq = 1000, 5000
        self.p.append(tcp(client, server, cport, sport, SYN, self.cseq))
        self.p.append(tcp(server, client, sport, cport, SYN | ACK, self.sseq, self.cseq + 1))
        self.cseq += 1
        self.sseq += 1
        self.p.append(tcp(client, server, cport, sport, ACK, self.cseq, self.sseq))

    def client_says(self, data):
        self.p.append(tcp(self.c, self.s, self.cp, self.sp, PSH | ACK, self.cseq, self.sseq, data))
        self.cseq += len(data)

    def server_says(self, data):
        self.p.append(tcp(self.s, self.c, self.sp, self.cp, PSH | ACK, self.sseq, self.cseq, data))
        self.sseq += len(data)

    def close(self):
        self.p.append(tcp(self.c, self.s, self.cp, self.sp, FIN | ACK, self.cseq, self.sseq))
        self.p.append(tcp(self.s, self.c, self.sp, self.cp, FIN | ACK, self.sseq, self.cseq + 1))
        self.p.append(tcp(self.c, self.s, self.cp, self.sp, ACK, self.cseq + 1, self.sseq + 1))


def http_get(packets, client, cport, path):
    s = Session(packets, client, WEB, cport, 80)
    s.client_says(f"GET {path} HTTP/1.1\r\nHost: {WEB}\r\nUser-Agent: Mozilla/5.0\r\n\r\n".encode())
    s.server_says(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 13\r\n\r\n<h1>Lab</h1>\n")
    s.close()


def build():
    """Returns a list of phases; each phase is a list of packets."""
    phases = []
    p = []
    # 1. normal traffic
    dns_query = struct.pack("!HHHHHH", 0x1234, 0x0100, 1, 0, 0, 0) + b"\x07college\x03edu\x00\x00\x01\x00\x01"
    p.append(udp(STAFF, "192.168.1.1", 53000, 53, dns_query))
    http_get(p, STAFF, 50001, "/index.html")
    phases.append(p)
    p = []
    # 2. ping sweep
    for i, host in enumerate((1, 10, 15, 20, 30)):
        p.append(icmp_echo(ATTACKER, f"192.168.1.{host}", i + 1))
    phases.append(p)
    p = []
    # 3. SYN scan
    for port in (21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3306, 3389, 8080):
        p.append(tcp(ATTACKER, WEB, 40000 + port, port, SYN, 7000))
        p.append(tcp(WEB, ATTACKER, port, 40000 + port, RST | ACK, 0, 7001))
    # 4. XMAS scan
    p.append(tcp(ATTACKER, WEB, 41000, 22, FIN | PSH | URG, 8000))
    phases.append(p)
    p = []
    # 5. web attacks
    http_get(p, ATTACKER, 42001, "/login.php?user=admin'%20OR%20'1'='1&pass=x")
    http_get(p, ATTACKER, 42002, "/item.php?id=1%20UNION%20SELECT%20user,password%20FROM%20users")
    http_get(p, ATTACKER, 42003, "/view.php?file=../../../../etc/passwd")
    phases.append(p)
    p = []
    # 6. FTP cleartext login
    s = Session(p, ATTACKER, FTP, 43001, 21)
    s.server_says(b"220 Lab FTP server ready\r\n")
    s.client_says(b"USER admin\r\n")
    s.server_says(b"331 Password required\r\n")
    s.client_says(b"PASS admin@123\r\n")
    s.server_says(b"230 Login successful\r\n")
    s.close()
    phases.append(p)
    # 7. Telnet attempt
    phases.append([tcp(ATTACKER, WEB, 44001, 23, SYN, 9000)])
    return phases


def write_pcap(path, phases):
    """Packets 50 ms apart inside a phase, 30 s pause between phases (like a real attacker)."""
    count = 0
    with open(path, "wb") as f:
        f.write(struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1))   # global header, Ethernet
        ts = 1793689200.0
        for phase in phases:
            for pkt in phase:
                f.write(struct.pack("<IIII", int(ts), int(ts % 1 * 1e6), len(pkt), len(pkt)) + pkt)
                ts += 0.05
                count += 1
            ts += 30
    return count


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "test_traffic.pcap")
    count = write_pcap(path, build())
    print(f"Wrote {count} packets to {path}")
