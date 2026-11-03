# Assignment 3: Detect and Prohibit a Wi-Fi Password Cracking Attempt

**Scenario:** someone on the road outside keeps trying passwords on the office Wi-Fi to reach the IP printer. `wifi_guard.py` watches the access point, detects the attempt and blocks the attacker. If the password is cracked anyway, it cuts the attacker off from the printer.

## 1. Network Setup (IEEE 802.11)

```
 Attacker (road) ~~~ Wi-Fi ~~~┐
 Staff laptops   ~~~ Wi-Fi ~~~┤ wlan0 192.168.4.1           eth0 192.168.5.1
                              │ [ Linux / Raspberry Pi AP ]────────────── IP printer 192.168.5.50
                              │   hostapd + dnsmasq + iptables + wifi_guard.py
```

The printer is on the **wired** side, so every Wi-Fi → printer packet is routed through the AP, where iptables can filter it.

### Hardware
- A Linux machine (Raspberry Pi 4 / laptop with Ubuntu)
- A USB Wi-Fi adapter that supports **AP mode**. Check with `iw list`: "Supported interface modes" must include `AP`. Chipsets: Atheros AR9271, Ralink RT5370, MediaTek MT7612U.

### Configure the Wi-Fi adapter as an Access Point

```bash
sudo apt install hostapd dnsmasq iptables
sudo ip addr add 192.168.4.1/24 dev wlan0
sudo ip addr add 192.168.5.1/24 dev eth0        # printer side
```

`/etc/hostapd/hostapd.conf`:
```ini
interface=wlan0
driver=nl80211
ssid=Office-WiFi
hw_mode=g                 # IEEE 802.11g, 2.4 GHz
channel=6
ieee80211n=1              # 802.11n
wpa=2                     # WPA2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP         # AES
wpa_passphrase=Str0ng-Office#2026
macaddr_acl=0             # allow all except the deny list
deny_mac_file=/etc/hostapd/hostapd.deny
ap_isolate=1              # Wi-Fi clients cannot talk to each other directly
ctrl_interface=/var/run/hostapd
logger_syslog=-1
logger_syslog_level=2
```

`/etc/dnsmasq.conf`:
```ini
interface=wlan0
dhcp-range=192.168.4.20,192.168.4.100,12h
log-dhcp
```

Start everything:
```bash
sudo touch /etc/hostapd/hostapd.deny
sudo sysctl -w net.ipv4.ip_forward=1
sudo hostapd -t /etc/hostapd/hostapd.conf > /var/log/hostapd.log 2>&1 &
sudo systemctl restart dnsmasq
```

## 2. Run the Detector

```bash
python wifi_guard.py --simulate                         # demo, no hardware needed
sudo python3 wifi_guard.py --follow /var/log/hostapd.log --allow allowed_macs.txt --enforce
```

`allowed_macs.txt` lists the staff devices' MAC addresses, one per line.

## 3. Detection Rules

| Rule | Evidence in the log | Attack it catches | Response |
| --- | --- | --- | --- |
| R1 Brute force | ≥ 5 `AP-STA-POSSIBLE-PSK-MISMATCH` from one MAC in 60 s | Guessing passwords one after another | MAC added to the hostapd deny list and disconnected |
| R2 MAC rotation | ≥ 8 mismatches from ≥ 4 MACs in 60 s | Attacker changes MAC to dodge R1 | All those MACs blocked (registered staff never blocked) |
| R3 Deauth attack | ≥ 3 clients `AP-STA-DISCONNECTED` within 10 s | `aireplay-ng --deauth` to capture the WPA handshake for offline cracking (`aircrack-ng`) | Alert: switch to WPA3 / enable 802.11w (PMF) |
| R4 Unknown device | DHCP lease to a MAC not in the allowlist | Password already cracked | MAC blocked + iptables DROP to printer ports 9100 / 631 / 515 |

Commands run on `--enforce`:
```bash
hostapd_cli -i wlan0 deny_acl ADD_MAC de:ad:be:ef:13:37
hostapd_cli -i wlan0 disassociate de:ad:be:ef:13:37
iptables -I FORWARD -s 192.168.4.66 -d 192.168.5.50 -p tcp --dport 9100 -j DROP
```

## 4. Demonstration Steps (in the lab)
1. Connect a staff phone with the correct password: `AP-STA-CONNECTED` appears and nothing is blocked.
2. From another phone, try 5 wrong passwords: **R1** fires. After that the phone cannot join even with the correct password, because its MAC is on the deny list.
3. Run `sudo aireplay-ng --deauth 5 -a <AP BSSID> wlan1mon` from a second adapter in monitor mode (only on your own lab network): **R3** fires.
4. Connect an unregistered laptop with the right password: **R4** fires, it is disconnected, and any printing attempt to 192.168.5.50 (ports 9100 / 631 / 515) is dropped.
5. `sudo iptables -L FORWARD -n` shows the DROP rules; `cat /etc/hostapd/hostapd.deny` shows the blocked MACs.

## 5. Extra Hardening
- Use **WPA3-SAE** (`wpa_key_mgmt=SAE`): it resists offline dictionary attacks even when a handshake is captured.
- Enable **802.11w** Protected Management Frames (`ieee80211w=2`): forged deauth frames are ignored.
- Use a long random passphrase and put the printer on its own VLAN.

> Only test deauthentication and password attacks on a network you own or have written permission to test.
