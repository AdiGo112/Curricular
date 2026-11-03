# Assignment 3: Wi-Fi Intrusion Detection and Prevention (IEEE 802.11 Access Point)

## Aim

A person on a nearby road is trying to enter into a WiFi network by trying to crack the Password to use the IP Printer resource; write a program to detect such an attempt and prohibit the access. Develop the necessary scenario by using an IEEE 802.11, configure a Wi-Fi adapter and Access Point.

> The folder's own `3_WiFiIntrusionDetection/README.md` has the full hardware list, `hostapd.conf`, `dnsmasq.conf` and lab steps. This note explains the concepts and the code, and does not repeat the config files.

## Theory and Fundamentals

### IEEE 802.11
IEEE 802.11 is the family of standards for Wi-Fi (wireless LAN). Common versions: 802.11b/g/n on 2.4 GHz, 802.11a/n/ac/ax on 5 GHz. An **Access Point (AP)** connects wireless **stations (STA)** to the wired network. The network name is the **SSID**; the AP's MAC address is the **BSSID**. A station goes through *scan -> authenticate -> associate*, then (for WPA2) the key handshake.

### Wi-Fi security generations
| Standard | Notes |
| --- | --- |
| WEP | Broken, crackable in minutes |
| WPA / WPA2-PSK (AES-CCMP) | Pre-Shared Key: everyone uses one passphrase. Used in this lab |
| WPA3-SAE | Resists offline dictionary attacks, forward secrecy |

### WPA2-PSK and the 4-way handshake
The passphrase and SSID produce the **PMK** (Pairwise Master Key). When a client joins, the AP and client run a **4-way handshake** to derive a fresh session key (PTK) without sending the key. If the client's passphrase is wrong, the handshake fails and `hostapd` logs `AP-STA-POSSIBLE-PSK-MISMATCH`.

### How a Wi-Fi password is cracked
1. **Online guessing:** try one password after another against the AP. Each failure appears in the log (this is what the program counts).
2. **Offline cracking:** capture the 4-way handshake over the air, then test millions of passphrases on a PC (`aircrack-ng`, `hashcat`). The AP sees nothing. To capture a handshake quickly the attacker sends **deauthentication** frames, which are unauthenticated management frames in 802.11 that force a client to disconnect and reconnect.
3. **Weak passphrase** is the real cause of success in both cases.

### Defence tools used in the scenario
- **hostapd:** Linux daemon that turns a Wi-Fi adapter into an AP (needs a card/driver that supports **AP mode**, check with `iw list`). It writes the events we parse.
- **dnsmasq:** DHCP/DNS server; logs `DHCPACK` when a client gets an IP address.
- **MAC filtering:** allow or deny by MAC address (`deny_mac_file`, or live with `hostapd_cli deny_acl`). It is only a speed-bump: MAC addresses can be spoofed or randomised, so it must be combined with other measures.
- **iptables:** Linux firewall. The printer is on the wired side, so Wi-Fi to printer traffic is *forwarded* through the AP and the `FORWARD` chain can DROP it. The printer ports are 9100 (RAW/JetDirect), 631 (IPP) and 515 (LPD).
- **802.11w (Protected Management Frames):** makes forged deauthentication frames ignored.
- **WIDS/WIPS:** Wireless Intrusion Detection / Prevention System, which is what `wifi_guard.py` is a small version of.
- **Allowlist:** list of registered staff MAC addresses; anything else that gets an IP is suspicious.

## How the Code Works

File: `3_WiFiIntrusionDetection/wifi_guard.py` (standard library only). It reads log lines (from a file, a live-followed file, or a simulation), turns them into events and applies four rules.

### Settings and event patterns
```python
PRINTER_IP = "192.168.5.50"
PRINTER_PORTS = (9100, 631, 515)
BRUTE_LIMIT, BRUTE_WINDOW = 5, 60
ROTATE_LIMIT, ROTATE_MACS, ROTATE_WINDOW = 8, 4, 60
DEAUTH_LIMIT, DEAUTH_WINDOW = 3, 10
```
`EVENTS` is a list of regular expressions for four log messages: `AP-STA-POSSIBLE-PSK-MISMATCH`, `AP-STA-CONNECTED`, `AP-STA-DISCONNECTED` and `DHCPACK(...) <ip> <mac>`. `parse_time()` understands both the `hostapd -t` epoch timestamp and normal syslog timestamps.

### The `WifiGuard` class
`feed(line)` finds the matching pattern and calls `on_<event>()`. Sliding windows are `deque`s whose old entries are removed by `_trim()`.

| Rule | Handler | Condition | Response |
| --- | --- | --- | --- |
| **R1 Brute force** | `on_psk_mismatch` | >= 5 mismatches from **one MAC** in 60 s | alert + `block()` |
| **R2 MAC rotation** | `on_psk_mismatch` | >= 8 mismatches from >= 4 **different MACs** in 60 s | block every MAC in the window that never connected successfully |
| **R3 Deauth attack** | `on_disconnected` | >= 3 distinct clients disconnected within 10 s | alert only (advice: WPA3 / 802.11w) |
| **R4 Unknown device** | `on_dhcp` | a MAC **not in the allowlist** receives a DHCP lease | alert + `block()` incl. printer iptables rules |

Details worth knowing:
- `on_connected` adds the MAC to `trusted` and clears its mismatch counter (a staff member who typed the password wrong once and then succeeded is not punished). R2 never blocks `trusted` MACs.
- R4 only runs when an allowlist is given (`--allow file`; the simulation supplies its own).
- If a MAC that is already blocked still gets an IP, `on_dhcp` calls `block()` again so the iptables rules are added.

### The response: `block(mac, ...)`
```python
cmds = [["hostapd_cli", "-i", INTERFACE, "deny_acl", "ADD_MAC", mac],
        ["hostapd_cli", "-i", INTERFACE, "disassociate", mac]]
ip = self.ip_of.get(mac)
if ip:
    for port in PRINTER_PORTS:
        cmds.append(["iptables", "-I", "FORWARD", "-s", ip, "-d", PRINTER_IP,
                     "-p", "tcp", "--dport", str(port), "-j", "DROP"])
```
Without `--enforce` the commands are only printed ("would run: ..."). With `--enforce` they run through `subprocess.run`; the program refuses to start unless it is Linux and root. The `ip_of` table (MAC to IP) is filled from DHCP events, which is how the program knows which IP to cut off from the printer.

### Simulation
`simulated_log()` builds a hostapd-style log (also saved as `simulated_hostapd.log`): 3 staff devices join; one staff typo; the attacker (`de:ad:be:ef:13:37`) tries 7 passwords; a deauth burst hits the 3 staff devices; 9 wrong passwords from random MACs follow; finally an unknown device `66:77:88:99:aa:bb` joins and gets IP 192.168.4.66. The script ends with assertions that all four rules fired and staff MACs were never blocked.

## How to Run and Expected Output

```bash
python LP4/CSDF/3_WiFiIntrusionDetection/wifi_guard.py --simulate        # no hardware needed
python LP4/CSDF/3_WiFiIntrusionDetection/wifi_guard.py hostapd.log --allow allowed_macs.txt   # analyse a log
sudo python3 wifi_guard.py --follow /var/log/hostapd.log --allow allowed_macs.txt --enforce   # live, on the AP
```

Real output of `--simulate` (trimmed):

```
[21:02:04] ALERT R1 BRUTE-FORCE: de:ad:be:ef:13:37 entered a wrong password 5 times in 60s
[21:02:04] BLOCK de:ad:be:ef:13:37 (password guessing)
    would run: hostapd_cli -i wlan0 deny_acl ADD_MAC de:ad:be:ef:13:37
[21:03:22] ALERT R3 DEAUTH-ATTACK: 3 clients dropped within 10s - ...
[21:05:28] ALERT R2 MAC-ROTATION: 8 wrong passwords from 8 different MACs in 60s ...
[21:15:01] ALERT R4 UNKNOWN-DEVICE: 66:77:88:99:aa:bb joined with the correct password ...
[21:15:01] BLOCK 66:77:88:99:aa:bb (unregistered device), IP 192.168.4.66 cut off from printer
    would run: iptables -I FORWARD -s 192.168.4.66 -d 192.168.5.50 -p tcp --dport 9100 -j DROP
Summary: 4 alerts, 10 devices blocked: [...]
Self-check passed: all four attack patterns detected, intruder cut off from the printer, staff devices untouched.
```

Observation: R1 fires on the **5th** wrong attempt, not the 7th, so the attacker is blocked early; the 8 random MACs of R2 plus the first attacker plus the unknown device make 10 blocked devices.

`--enforce` and the lab steps (connect staff phone, try 5 wrong passwords from another phone, `aireplay-ng --deauth`, join with an unregistered laptop, `iptables -L FORWARD -n`) need a real Linux AP, see the folder README. Run attacks only on your own lab network.

## Related Concepts and Real-World Tools

- **aircrack-ng suite** (`airodump-ng`, `aireplay-ng`, `aircrack-ng`): capture handshakes, send deauth, crack passphrases. Used here only to *simulate* the attacker.
- **Kismet, Wireshark (monitor mode), `iw`, `hostapd_cli`:** wireless monitoring and AP control.
- **WIPS products:** Cisco CleanAir / Aruba RFProtect, open-source **Kismet** alerts, **Wazuh** for log based detection.
- **Fail2ban:** the same idea (count failures in logs, then ban) for SSH/web.
- **WPA3-SAE, 802.11w (PMF), WPA2-Enterprise (802.1X / RADIUS)** with per-user credentials, and **VLAN** separation for the printer.
- **Rogue AP / Evil Twin:** another Wi-Fi attack; handled by WIPS.
- **IT Act 2000:** Section 43 (unauthorised access to a computer network) and Section 66 (punishment when done dishonestly), also Section 66F if cyber terrorism. Section 69/72 apply to monitoring and privacy when you capture other people's traffic.

## Viva Questions

1. **What does `AP-STA-POSSIBLE-PSK-MISMATCH` mean?** hostapd saw a client fail the WPA2 4-way handshake, most likely because it used the wrong passphrase. Counting these per MAC detects online guessing.
2. **Explain the WPA2 4-way handshake.** AP and client prove they know the PMK (derived from passphrase + SSID) and derive a fresh session key by exchanging random numbers (nonces), without sending the passphrase. A captured handshake allows offline cracking.
3. **What is a deauthentication attack and why is it used?** The attacker sends forged management frames that disconnect clients; when they reconnect, the attacker captures the handshake for offline cracking. Rule R3 spots several clients dropping together; 802.11w prevents it.
4. **Why is MAC filtering alone not secure?** MAC addresses are visible over the air and can be changed in software. That is why R2 handles MAC rotation and R4 uses an allowlist.
5. **Why is the printer connected on the wired side?** Then every Wi-Fi to printer packet is routed through the AP where iptables can filter it; traffic between two Wi-Fi clients in the same BSS would not pass through the firewall.
6. **What do the iptables commands do?** `iptables -I FORWARD -s <ip> -d 192.168.5.50 -p tcp --dport 9100 -j DROP` inserts a rule that drops that client's packets to the printer's port. The code does this for 9100, 631 and 515.
7. **How does the program avoid blocking legitimate staff?** A successful connection marks the MAC as trusted and resets its counter, R2 skips trusted MACs, and R1 needs 5 failures inside 60 s.
8. **Why is `--enforce` separate from detection?** Detection is safe to test anywhere; blocking needs Linux, root and a real AP, and a false positive would lock a real user out, so commands are printed first.
9. **How do you make the network stronger than this detection?** Use WPA3-SAE or a long random WPA2 passphrase, enable 802.11w, use WPA2-Enterprise, and put the printer in its own VLAN.
10. **What is the difference between IDS and IPS here?** Detecting and alerting is IDS; automatically blocking the MAC and cutting printer access is IPS behaviour.
