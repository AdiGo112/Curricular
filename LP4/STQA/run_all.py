# Runs every STQA program / test suite and prints a PASS/FAIL table.
#   python run_all.py            (also the default command of the Docker image)
#
# Selenium suites run headless. Assignment 5 needs internet (it opens selenium.dev).

import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

PROGRAMS = [
    ("2  Gmail login scenarios", [PY, "2_GmailLoginTest.py"], "."),
    ("3  Social media test cases (Excel)", [PY, "3_SocialMediaTestCases.py"], "."),
    ("5  Selenium WebDriver (needs internet)", [PY, "selenium_webdriver_test.py"], "5_Selenium"),
    ("7  COVID-19 regex tests (Python)", [PY, "test_regex.py"], "7_MiniProject_Covid19"),
    ("7  COVID-19 regex tests (JavaScript)", ["node", "test_regex.js"], "7_MiniProject_Covid19"),
    ("8  Library: unit + coverage", [PY, "run_tests.py"], "8_MiniProject_Library"),
    ("9  TaskTrack: unit + integration", [PY, "test_unit_integration.py"], "9_MiniProject_TestIntegration"),
    ("9  TaskTrack: Selenium regression", [PY, "test_selenium_regression.py"], "9_MiniProject_TestIntegration"),
]

if os.environ.get("COVID_URL"):                  # PHP site is running (Docker compose sets this)
    PROGRAMS.insert(5, ("7  COVID-19 site functional tests (PHP)", [PY, "test_site.py"], "7_MiniProject_Covid19"))

env = {**os.environ, "HEADLESS": "1"}
failed = skipped = 0
for name, cmd, folder in PROGRAMS:
    if not shutil.which(cmd[0]):
        print(f"SKIP  {name:40} ({cmd[0]} not installed)")
        skipped += 1
        continue
    start = time.time()
    result = subprocess.run(cmd, cwd=os.path.join(HERE, folder), env=env, capture_output=True, text=True, timeout=600)
    ok = result.returncode == 0
    failed += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {name:40} {time.time() - start:5.1f} s")
    if not ok:
        print("      " + "\n      ".join((result.stdout + result.stderr).strip().splitlines()[-8:]))

print(f"\n{len(PROGRAMS) - failed - skipped}/{len(PROGRAMS)} passed" + (f", {skipped} skipped" if skipped else ""))
sys.exit(1 if failed else 0)
