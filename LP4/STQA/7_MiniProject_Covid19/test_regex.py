# =========================================================
# REGEX TEST CASES (Python runner)
# =========================================================
#
# Runs every test case in regex_testcases.json against the
# patterns in regex_rules.json - the SAME files used by the
# PHP server code and the JavaScript in the browser.
#
# Each case: [ID, field, input, should_match, description]
#
# RUN:     python test_regex.py
# OUTPUT:  regex_test_report.txt
#
# =========================================================

import json
import os
import re
import sys

here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, "regex_rules.json")) as f:
    rules = json.load(f)
with open(os.path.join(here, "regex_testcases.json")) as f:
    cases = json.load(f)

lines = [f"{'ID':6}{'Field':11}{'Input':34}{'Expected':10}{'Actual':10}Result", "-" * 80]
passed = 0
for case_id, field, value, expected, desc in cases:
    actual = re.fullmatch(rules[field]["pattern"], value) is not None
    ok = actual == expected
    passed += ok
    shown = repr(value)[:32]
    lines.append(f"{case_id:6}{field:11}{shown:34}{'valid' if expected else 'invalid':10}"
                 f"{'valid' if actual else 'invalid':10}{'PASS' if ok else 'FAIL'}   {desc}")

total = len(cases)
lines += ["-" * 80, f"Total: {total}   Passed: {passed}   Failed: {total - passed}   "
                    f"Pass rate: {100 * passed / total:.1f}%"]

print("\n".join(lines))
with open(os.path.join(here, "regex_test_report.txt"), "w", encoding="utf-8") as f:
    f.write("COVID-19 Portal - Regular Expression Test Report (Python)\n\n" + "\n".join(lines) + "\n")

sys.exit(0 if passed == total else 1)
