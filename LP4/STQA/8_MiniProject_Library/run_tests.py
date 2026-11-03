# =========================================================
# TEST RUNNER + REPORT
# =========================================================
#
# 1. Runs all unit / integration tests (unittest)
# 2. Measures statement + branch coverage (coverage.py)
# 3. Writes test_report.txt with Pass/Fail per test case,
#    coverage, and the acceptance verdict
# 4. Writes an HTML coverage report in htmlcov/index.html
#    (green = executed line, red = not executed)
#
# Acceptance criteria (see test_plan.md):
#   all tests pass AND branch coverage >= 90%  -> ACCEPTED
#   pass rate >= 90% AND coverage >= 80%        -> ACCEPTED WITH MINOR DEFECTS
#   otherwise                                   -> REJECTED
#
# RUN:  pip install coverage
#       python run_tests.py
#
# =========================================================

import io
import os
import sys
import time
import unittest

import coverage

here = os.path.dirname(os.path.abspath(__file__))
os.chdir(here)
sys.path.insert(0, here)

cov = coverage.Coverage(branch=True, include=[os.path.join(here, "library.py")])
cov.start()

import test_library  # noqa: E402  (imported after coverage starts so library.py is measured)

suite = unittest.TestLoader().loadTestsFromModule(test_library)
tests = []
stack = [suite]
while stack:                       # flatten nested suites (the runner empties them later)
    item = stack.pop()
    if isinstance(item, unittest.TestSuite):
        stack.extend(reversed(list(item)))
    else:
        tests.append(item)

result = unittest.TextTestRunner(verbosity=2).run(suite)
cov.stop()
cov.save()

failed = {id(t): "FAIL" for t, _ in result.failures}
failed.update({id(t): "ERROR" for t, _ in result.errors})

buf = io.StringIO()
percent = cov.report(file=buf, show_missing=True)
cov.html_report(directory=os.path.join(here, "htmlcov"))

total = len(tests)
passed = total - len(failed)
rate = 100 * passed / total
if passed == total and percent >= 90:
    verdict = "ACCEPTED"
elif rate >= 90 and percent >= 80:
    verdict = "ACCEPTED WITH MINOR DEFECTS"
else:
    verdict = "REJECTED"

lines = ["=" * 78, " Library Management System - Test Report", f" Date: {time.strftime('%Y-%m-%d %H:%M')}",
         "=" * 78, f"{'Suite':22}{'Test case':38}{'Result':7}", "-" * 78]
for t in tests:
    suite_name, case = t.id().split(".")[-2:]
    lines.append(f"{suite_name:22}{case:38}{failed.get(id(t), 'PASS'):7}")
    lines.append(f"{'':22}  {t.shortDescription()}")
lines += ["-" * 78,
          f"Total: {total}   Passed: {passed}   Failed: {total - passed}   Pass rate: {rate:.1f}%",
          "", "Coverage (statement + branch):", buf.getvalue().rstrip(),
          "", f"Verdict: {verdict}"]
for t, trace in result.failures + result.errors:
    lines += ["", f"DEFECT in {t.id()}:", "    " + trace.strip().splitlines()[-1]]

with open("test_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"\nCoverage: {percent:.1f}%   Verdict: {verdict}")
print("Reports: test_report.txt, htmlcov/index.html")
sys.exit(0 if verdict == "ACCEPTED" else 1)
