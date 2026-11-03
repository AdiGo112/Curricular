# Assignment 6: Configure and Demonstrate Wireshark and SNORT

| File | Purpose |
| --- | --- |
| `make_test_traffic.py` | Writes `test_traffic.pcap`: 81 real packets of normal traffic + attacks (ping sweep, SYN scan, XMAS scan, SQL injection, path traversal, FTP cleartext login, Telnet) |
| `local.rules` | 8 custom Snort rules that detect those attacks |
| `mini_ids.py` | Applies `local.rules` to a pcap the way Snort does (works without Snort, for practice and checking) |

```bash
python make_test_traffic.py      # create the capture
python mini_ids.py               # 18 alerts, self-check
```

---

## Part A: Wireshark (Network Protocol Analyser)

### Install
- **Windows:** download from wireshark.org and install. Tick **Npcap** during setup (needed to capture live).
- **Ubuntu:** `sudo apt install wireshark`, answer **Yes** to "allow non-superusers to capture", then `sudo usermod -aG wireshark $USER` and log out and back in.

### Configure and Capture
1. Start Wireshark, choose the active interface (Wi-Fi / Ethernet) and click the blue fin to start.
2. Open a website, then stop the capture (red square).
3. **File → Save As** in *pcap* format to keep the evidence. **Statistics → Capture File Properties** shows the hashes.
4. Or open the lab file: **File → Open → test_traffic.pcap**.

### Display Filters to Demonstrate

| Filter | Shows |
| --- | --- |
| `icmp.type == 8` | Ping sweep (5 echo requests from 10.0.0.66) |
| `tcp.flags.syn == 1 && tcp.flags.ack == 0` | SYN scan, 15 ports probed |
| `tcp.flags.fin == 1 && tcp.flags.push == 1 && tcp.flags.urg == 1` | Nmap XMAS scan |
| `http.request` | All web requests, including the SQL injection |
| `http.request.uri contains "UNION"` | SQL injection request |
| `ftp.request.command == "PASS"` | **Cleartext FTP password: `admin@123`** |
| `ip.addr == 10.0.0.66` | Everything the attacker did |
| `dns` | Normal DNS query from the staff PC |

### Useful Features
- **Follow → TCP Stream** (right-click an FTP packet): shows the whole login conversation as text.
- **Statistics → Conversations** / **Endpoints**: who talked to whom, and how much.
- **Statistics → Protocol Hierarchy**: share of each protocol.
- **Analyze → Expert Information**: warnings such as resets and retransmissions.

---

## Part B: SNORT (Intrusion Detection System)

### Install
- **Ubuntu 22.04:** `sudo apt install snort` (Snort 2.9; enter your network, e.g. `192.168.1.0/24`, when asked).
- **Snort 3 / other OS:** download from snort.org and follow its install guide.
- **Windows:** Snort 2.9 installer from snort.org + Npcap.

Check: `snort -V`

### Configure
1. Copy the rules: `sudo cp local.rules /etc/snort/rules/local.rules`
2. In `/etc/snort/snort.conf` set the home network and include the local rules:
   ```
   ipvar HOME_NET 192.168.1.0/24
   include $RULE_PATH/local.rules
   ```
3. Test the configuration: `sudo snort -T -c /etc/snort/snort.conf`

### Run
```bash
# Offline: analyse the lab capture (or any Wireshark pcap)
sudo snort -r test_traffic.pcap -c /etc/snort/snort.conf -A console -q

# Live IDS on an interface
sudo snort -i eth0 -c /etc/snort/snort.conf -A console -q
```

From another machine, trigger live alerts on your own lab network:
```bash
ping 192.168.1.10                          # sid 1000001
nmap -sS 192.168.1.10                      # sid 1000002
nmap -sX 192.168.1.10                      # sid 1000003
curl "http://192.168.1.10/a.php?id=1%20UNION%20SELECT%201"   # sid 1000004
```

### Rule Anatomy
```
alert tcp any any -> $HOME_NET 80 (msg:"SQL injection - UNION SELECT"; content:"UNION"; nocase; content:"SELECT"; nocase; sid:1000004; rev:1;)
└─┬─┘ └┬┘ └──┬──┘    └────┬────┘ └───────────────────────── options ─────────────────────────────────────┘
action proto source   destination (network + port)
```

| Option | Meaning |
| --- | --- |
| `msg` | Text printed in the alert |
| `content` / `nocase` | Byte pattern that must appear in the payload / ignore case |
| `pcre` | Regular expression on the payload |
| `flags:S` | TCP flags must be exactly SYN |
| `itype:8` | ICMP type 8 = echo request |
| `detection_filter` | Alert only after *count* matches from one source within *seconds* (rate-based, used for scans) |
| `sid` / `rev` | Unique rule ID (≥ 1000000 for local rules) / revision |

### Expected Result (both Snort and `mini_ids.py`)

| SID | Alert | Count |
| --- | --- | --- |
| 1000001 | ICMP Ping | 5 |
| 1000002 | Possible SYN port scan (10th SYN onwards) | 6 |
| 1000003 | Nmap XMAS scan | 1 |
| 1000004 | SQL injection - UNION SELECT | 1 |
| 1000005 | SQL injection - OR 1=1 | 1 |
| 1000006 | Path traversal | 1 |
| 1000007 | FTP cleartext password | 1 |
| 1000008 | Telnet attempt (scan + real attempt) | 2 |

Normal DNS and HTTP traffic from the staff PC raises **no** alert.

## Wireshark vs Snort

| | Wireshark | Snort |
| --- | --- | --- |
| Type | Packet analyser (passive viewer) | Intrusion detection / prevention system |
| Use | Manual investigation, protocol debugging, evidence | Automatic, rule-based detection 24×7 |
| Output | Packets in a GUI | Alerts and logs |
| Can block traffic? | No | Yes, in inline IPS mode (`-Q`) |
