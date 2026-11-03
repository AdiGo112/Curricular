# Assignment 6: Configure and Demonstrate Wireshark and SNORT

## Aim

Configure and demonstrate use of a vulnerability assessment tool like Wireshark or SNORT.

> The folder's `6_WiresharkSnort/README.md` already lists the install steps, all Wireshark display filters, the Snort run commands and the expected alert table. This note explains the concepts and how the helper programs work, and refers to the README for the step-by-step lab.

## Theory and Fundamentals

### Packet capture and analysis
Data on a network travels as **packets**. A **packet capture** (pcap) is a file of recorded packets. A **packet sniffer / protocol analyser** such as **Wireshark** shows each packet layer by layer:

| Layer | Header | Fields we use |
| --- | --- | --- |
| Data link | Ethernet | MAC addresses, type `0x0800` = IPv4 |
| Network | IPv4 | Source/destination IP, protocol (1 ICMP, 6 TCP, 17 UDP) |
| Transport | TCP / UDP / ICMP | Ports, **TCP flags**, ICMP type |
| Application | HTTP, FTP, DNS, Telnet | Requests, commands, passwords |

Capturing needs a driver that puts the network card in **promiscuous mode** (Npcap on Windows, libpcap on Linux). **Display filters** (e.g. `http.request`) choose what to show; **capture filters** (BPF, e.g. `tcp port 80`) choose what to record.

### TCP flags and scans
TCP flags: **SYN, ACK, FIN, RST, PSH, URG**. A normal connection is the **3-way handshake** SYN -> SYN/ACK -> ACK.
- **SYN (half-open) scan:** attacker sends SYN to many ports; an open port replies SYN/ACK, a closed one RST. (`nmap -sS`)
- **XMAS scan:** FIN+PSH+URG together, a combination no normal traffic uses. (`nmap -sX`)
- **Ping sweep:** ICMP echo requests (type 8) to many hosts to find live machines.

### IDS and IPS
- **IDS (Intrusion Detection System):** watches traffic and **alerts**. Passive.
- **IPS (Intrusion Prevention System):** sits **inline** and **drops/blocks** bad traffic.
- **Signature (rule) based:** matches known patterns (Snort). **Anomaly based:** learns normal behaviour and flags deviations. **NIDS** watches the network, **HIDS** watches a host.

### Snort rule syntax
```
alert tcp any any -> $HOME_NET 80 (msg:"SQL injection - UNION SELECT"; content:"UNION"; nocase; content:"SELECT"; nocase; sid:1000004; rev:1;)
```
`action protocol source-ip source-port -> destination-ip destination-port (options)`. Common options: `msg`, `content` (+`nocase`), `pcre` (regex), `flags`, `itype`, `detection_filter` (rate threshold), `sid` (unique ID, local rules from 1,000,000) and `rev`. `$HOME_NET` is the protected network defined in `snort.conf`. The README has the full option table.

### Wireshark vs Snort
Wireshark is for manual investigation and evidence (a viewer); Snort runs automatically 24x7 on rules and produces alerts, and can block in inline IPS mode. They complement each other: Snort raises the alert, Wireshark proves what happened.

### "Vulnerability assessment" in this context
Strictly, scanners such as Nessus/OpenVAS find weaknesses; Wireshark/Snort are monitoring tools that reveal **insecure protocols** (cleartext FTP/Telnet passwords) and **attacks** against weaknesses. The lab uses them to assess what an attacker can see and do.

## How the Code Works

Three files in `6_WiresharkSnort/`, all standard library.

### 1. `make_test_traffic.py`: builds `test_traffic.pcap`
It constructs packets **byte by byte** with `struct` (Ethernet + IPv4 + TCP/UDP/ICMP, with correct checksums), so Wireshark and Snort accept the file. The `Session` class performs a real TCP handshake, data exchange and close so *Follow TCP Stream* works. `build()` returns phases:

1. Normal DNS query and an HTTP page visit from staff PC 192.168.1.15.
2. Ping sweep from attacker 10.0.0.66 to 5 hosts.
3. SYN scan of 15 ports on the web server 192.168.1.10, plus one XMAS packet.
4. HTTP requests with SQL injection (`OR '1'='1`, `UNION SELECT`) and path traversal (`../../../../etc/passwd`).
5. FTP login with cleartext `PASS admin@123`.
6. One Telnet SYN.

`write_pcap()` writes the pcap global header, spaces packets 50 ms apart and puts 30 s between phases. Result: **81 packets**.

### 2. `local.rules`: 8 Snort rules
| SID | Detects | Key options |
| --- | --- | --- |
| 1000001 | ICMP ping | `itype:8` |
| 1000002 | SYN port scan | `flags:S; detection_filter:track by_src, count 10, seconds 5` |
| 1000003 | XMAS scan | `flags:FPU` |
| 1000004 | SQLi UNION SELECT | two `content` + `nocase`, port 80 |
| 1000005 | SQLi OR 1=1 | `pcre` |
| 1000006 | Path traversal | `content:"../"` |
| 1000007 | FTP cleartext password | `content:"PASS "`, port 21 |
| 1000008 | Telnet attempt | `flags:S`, port 23 |

### 3. `mini_ids.py`: a tiny Snort
- `parse_rules()` reads each rule with a regex for the header and then another regex for the `key:value;` options.
- `read_pcap()` parses the pcap file; `decode()` extracts IPs, ports, TCP flags, ICMP type and payload.
- `matches(rule, pkt)` checks protocol, addresses, ports, ICMP type, **exact** TCP flag set, every `content`, and `pcre`:
```python
wanted = sum(FLAG_BITS[c] for c in rule["flags"] if c in FLAG_BITS)
if pkt["flags"] & 0x3F != wanted:      # exact flag set, like Snort's flags:S
    return False
```
- `run()` implements `detection_filter`: a per-(rule, source IP) queue of timestamps; alerts only start once `count` matches fall within `seconds`. That is why the SYN scan alerts begin at the 10th SYN (6 alerts for 15 ports).
- Output imitates Snort: `[**] [1:1000004:1] message [**] {TCP} src:port -> dst:port`.

Supported options are only those listed in the file header (`msg, sid, content, nocase, pcre, flags, itype, detection_filter`); `HOME_NET` is fixed to 192.168.1.0/24 in the script.

## How to Run and Expected Output

```bash
cd LP4/CSDF/6_WiresharkSnort
python make_test_traffic.py        # creates test_traffic.pcap (81 packets)
python mini_ids.py                 # 18 alerts + self-check
python mini_ids.py capture.pcap    # your own Wireshark capture (pcap, not pcapng)
```

Real output (trimmed):

```
Loaded 8 rules from local.rules; reading test_traffic.pcap
[**] [1:1000001:1] ICMP Ping (echo request) [**]  {ICMP} 10.0.0.66 -> 192.168.1.1
[**] [1:1000008:1] Telnet connection attempt [**]  {TCP} 10.0.0.66:40023 -> 192.168.1.10:23
[**] [1:1000002:1] Possible SYN port scan [**]  {TCP} 10.0.0.66:40143 -> 192.168.1.10:143
[**] [1:1000003:1] Nmap XMAS scan [**]  {TCP} 10.0.0.66:41000 -> 192.168.1.10:22
[**] [1:1000005:1] SQL injection - OR 1=1 [**]  ...
81 packets analysed, 18 alerts
  sid 1000001    5  ICMP Ping (echo request)
  sid 1000002    6  Possible SYN port scan
  sid 1000008    2  Telnet connection attempt
Self-check passed: every rule fired the expected number of times, normal traffic raised no alert.
```

**Wireshark part (manual, see README):** open `test_traffic.pcap`; apply `tcp.flags.syn == 1 && tcp.flags.ack == 0`, `http.request.uri contains "UNION"`, `ftp.request.command == "PASS"` (shows `admin@123`); right-click -> *Follow -> TCP Stream*; *Statistics -> Conversations / Protocol Hierarchy*. **Snort part:** copy `local.rules`, set `HOME_NET`, `snort -T -c /etc/snort/snort.conf`, then `sudo snort -r test_traffic.pcap -c /etc/snort/snort.conf -A console -q`; the alert counts should match the table above.

## Related Concepts and Real-World Tools

- **Wireshark / tshark / tcpdump:** capture and analysis; TShark is the command-line Wireshark.
- **Snort 2/3, Suricata, Zeek (Bro):** Suricata is multi-threaded and Snort-rule compatible; Zeek produces rich protocol logs and scripts instead of simple rules.
- **Security Onion:** Linux distribution bundling Snort/Suricata, Zeek and dashboards.
- **Vulnerability scanners:** **Nessus, OpenVAS/Greenbone, Nikto, Nmap scripts (NSE)**.
- **Metasploit / Burp Suite:** exploitation and web testing (only with permission).
- **Rule sources:** Snort community rules, Emerging Threats, Talos.
- **Encryption problem:** HTTPS/TLS hides payloads, so signature IDS cannot see inside; use TLS inspection or host sensors.
- **Evidence handling:** save pcap, hash it (Wireshark *Capture File Properties*), record who captured it.
- **Legal:** sniffing other people's traffic without authority violates IT Act 2000 Section 43 / 66 and Section 69 / 72 (interception, privacy); capture only your own lab network.

## Viva Questions

1. **What is Wireshark and what is Snort?** Wireshark is a packet analyser used to view and investigate traffic. Snort is a rule-based IDS/IPS that alerts on or blocks suspicious packets.
2. **Difference between IDS and IPS?** IDS only detects and alerts; IPS is inline and can drop the packets. Snort does both depending on mode (`-Q` inline).
3. **Explain a Snort rule.** `action proto src_ip src_port -> dst_ip dst_port (options)`, e.g. `alert tcp any any -> $HOME_NET 80 (msg:"..."; content:"UNION"; sid:1000004;)`. The header says which traffic to look at, the options say what to match.
4. **What is a SYN scan and how does the rule detect it?** Many SYN packets to different ports. Rule 1000002 uses `flags:S` with `detection_filter` (10 in 5 s from one source), so normal single connections do not alert.
5. **What is an XMAS scan?** A packet with FIN, PSH and URG set (`flags:FPU`), a combination that does not occur in normal traffic.
6. **Why does the SYN/ACK from the server not trigger the scan rule?** `flags:S` means the flags must be exactly SYN; SYN/ACK has the ACK bit as well. The mini IDS compares the exact flag set.
7. **How does Wireshark show the cleartext FTP password?** Filter `ftp.request.command == "PASS"` or *Follow TCP Stream*; FTP and Telnet send passwords unencrypted, which is why SSH/SFTP should be used.
8. **What is the difference between a capture filter and a display filter?** Capture filters (BPF syntax) limit what is recorded; display filters hide packets already captured.
9. **What does `$HOME_NET` mean?** The variable in `snort.conf` holding the protected network range; rules use it to decide the destination of interest.
10. **What are the limits of signature-based IDS?** It misses unknown attacks and encrypted payloads, and needs constant rule updates and tuning to limit false positives.
