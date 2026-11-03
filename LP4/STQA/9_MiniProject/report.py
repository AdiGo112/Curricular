# =========================================================
# TEST REPORT GENERATOR
# =========================================================
#
# Runs a unittest suite and writes a Pass/Fail report.
#
# Acceptance criteria (from test_plan.md):
#   Pass rate 100%          -> ACCEPTED
#   Pass rate >= 90%        -> ACCEPTED WITH MINOR DEFECTS
#   Pass rate <  90%        -> REJECTED
#
# =========================================================

import re
import time
import unittest


def run_and_report(test_classes, title, report_file):
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(loader.loadTestsFromTestCase(c) for c in test_classes)
    tests = list(_all_tests(suite))   # collect first: the runner empties the suite

    result = unittest.TextTestRunner(verbosity=2).run(suite)

    failed = {id(t): "FAIL" for t, _ in result.failures}
    failed.update({id(t): "ERROR" for t, _ in result.errors})
    rows = []
    for test in tests:
        status = failed.get(id(test), "PASS")
        rows.append((test.id().split(".", 1)[1], test.shortDescription() or "", status))

    total = len(rows)
    passed = sum(1 for r in rows if r[2] == "PASS")
    rate = 100 * passed / total if total else 0
    if rate == 100:
        verdict = "ACCEPTED"
    elif rate >= 90:
        verdict = "ACCEPTED WITH MINOR DEFECTS"
    else:
        verdict = "REJECTED"

    lines = [
        "=" * 70,
        f" {title}",
        f" Date: {time.strftime('%Y-%m-%d %H:%M')}",
        "=" * 70,
        f"{'Test Case':45} {'Result':8}",
        "-" * 70,
    ]
    for name, desc, status in rows:
        lines.append(f"{name:45} {status:8}")
        if desc:
            lines.append(f"    {desc}")
    lines += [
        "-" * 70,
        f"Total: {total}   Passed: {passed}   Failed: {total - passed}   Pass rate: {rate:.1f}%",
        f"Verdict: {verdict}",
    ]
    for test, trace in result.failures + result.errors:
        error_line = next((l for l in trace.splitlines() if re.match(r"\w[\w.]*(Error|Exception)", l)),
                          trace.strip().splitlines()[-1])
        lines += ["", f"DEFECT in {test.id()}:", "    " + error_line]

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nReport written to {report_file}  ->  {verdict}")
    return result.wasSuccessful()


def _all_tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _all_tests(item)
        else:
            yield item
