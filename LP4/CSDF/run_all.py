# Runs every CSDF demo / self-check and prints a PASS/FAIL table.
#   python run_all.py            (also the default command of the Docker image)

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

PROGRAMS = [
    ("1  Email header analysis", "1_EmailHeaderAnalysis/email_header_analyzer.py", ["--demo"]),
    ("2  CAPTCHA", "2_CAPTCHA/captcha.py", ["--test"]),
    ("3  Wi-Fi intrusion detection", "3_WiFiIntrusionDetection/wifi_guard.py", ["--simulate"]),
    ("4  Deleted file/partition recovery", "4_DataRecovery/recover.py", ["--demo"]),
    ("5  Log capture + correlation", "5_LogCorrelation/log_correlator.py", ["--demo"]),
    ("6  Snort rules / mini IDS", "6_WiresharkSnort/mini_ids.py", []),
    ("7  Honeypot", "7_Honeypot/honeypot.py", ["--demo"]),
    ("8  Image forensics", "8_ImageForensics/image_forensics.py", ["--demo"]),
    ("9  Audio forensics", "9_AudioForensics/audio_forensics.py", ["--demo"]),
    ("10 Video forensics", "10_VideoForensics/video_forensics.py", ["--demo"]),
    ("11 Cyber crime analysis (CIA)", "11_CyberCrimeAnalysis/forensic_system.py", []),
]

failed = 0
for name, script, args in PROGRAMS:
    path = os.path.join(HERE, script)
    start = time.time()
    result = subprocess.run([sys.executable, path, *args], cwd=os.path.dirname(path),
                            capture_output=True, text=True, timeout=300)
    ok = result.returncode == 0
    failed += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {name:38} {time.time() - start:5.1f} s")
    if not ok:
        print("      " + "\n      ".join((result.stdout + result.stderr).strip().splitlines()[-8:]))

print(f"\n{len(PROGRAMS) - failed}/{len(PROGRAMS)} passed")
sys.exit(1 if failed else 0)
