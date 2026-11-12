# =========================================================
# TEST REPORT GENERATOR
# =========================================================
#
# Runs a unittest suite and returns the report as text tables:
#   summary, test results, bugs identified, plus any extra
#   sections (e.g. the exploratory session).
# Each test's docstring is "ID: description [bug type, severity]";
# the type and severity are the bug class if that test fails.
#
# Acceptance criteria (from test_plan.md):
#   Pass rate 100%          -> ACCEPTED
#   Pass rate >= 90%        -> ACCEPTED WITH MINOR DEFECTS
#   Pass rate <  90%        -> REJECTED
#
# =========================================================

import re
import textwrap
import time
import unittest


class TimedResult(unittest.TextTestResult):
    """Records how many seconds each test took."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seconds = {}

    def startTest(self, test):
        self._start = time.perf_counter()
        super().startTest(test)

    def stopTest(self, test):
        self.seconds[test.id()] = time.perf_counter() - self._start
        super().stopTest(test)


def table(headers, rows, widths):
    """Plain-text grid table; long cells wrap inside their column."""
    line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def row_lines(cells):
        wrapped = [textwrap.wrap(str(c), w) or [""] for c, w in zip(cells, widths)]
        return ["| " + " | ".join((col[i] if i < len(col) else "").ljust(w) for col, w in zip(wrapped, widths)) + " |"
                for i in range(max(map(len, wrapped)))]

    out = [line, *row_lines(headers), line.replace("-", "=")]
    for r in rows:
        out += row_lines(r) + [line]
    return out


def heading(text):
    return ["", text, "-" * len(text)]


def parse_doc(test):
    """'RT-03: Password ... [Validation/Input, Major]' -> (id, description, type, severity)."""
    m = re.match(r"(\S+): (.*?) \[(.*), (.*)\]$", test.shortDescription() or "")
    return m.groups() if m else (test.id().rsplit(".", 1)[-1], "", "", "")


def run_and_report(test_classes, title, extra=()):
    """Returns (all passed?, pass rate, verdict, report lines)."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(loader.loadTestsFromTestCase(c) for c in test_classes)
    tests = list(_all_tests(suite))   # collect first: the runner empties the suite

    start = time.perf_counter()
    result = unittest.TextTestRunner(verbosity=2, resultclass=TimedResult).run(suite)
    duration = time.perf_counter() - start   # includes starting the server and the browser

    status = {id(t): "FAIL" for t, _ in result.failures}
    status.update({id(t): "ERROR" for t, _ in result.errors})
    total = len(tests)
    passed = total - len(status)
    rate = 100 * passed / total if total else 0
    if rate == 100:
        verdict = "ACCEPTED"
    elif rate >= 90:
        verdict = "ACCEPTED WITH MINOR DEFECTS"
    else:
        verdict = "REJECTED"

    lines = ["=" * len(title), title, "=" * len(title)]
    lines += heading("1. Summary")
    lines += table(["Total", "Passed", "Failed", "Pass rate", "Duration (s)", "Verdict"],
                   [[total, passed, total - passed, f"{rate:.1f}%", f"{duration:.2f}", verdict]],
                   [5, 6, 6, 9, 12, 27])

    lines += heading("2. Test Results")
    rows = []
    for t in tests:
        tid, desc, btype, sev = parse_doc(t)
        rows.append([tid, desc, btype, sev, f"{result.seconds.get(t.id(), 0):.2f}", status.get(id(t), "PASS")])
    lines += table(["ID", "Test case", "Bug type if it fails", "Severity", "Time (s)", "Result"], rows,
                   [5, 40, 16, 8, 8, 6])

    lines += heading("3. Bugs Identified")
    bugs = result.failures + result.errors
    if not bugs:
        lines.append("None. Every test passed.")
    else:
        rows = []
        for t, trace in bugs:
            tid, desc, btype, sev = parse_doc(t)
            error = next((l for l in trace.splitlines() if re.match(r"\w[\w.]*(Error|Exception)", l)),
                         trace.strip().splitlines()[-1])
            error = re.sub(r"^selenium\.common\.exceptions\.", "", error)   # shorter evidence text
            rows.append([tid, desc, btype, sev, textwrap.shorten(error, 80, placeholder=" ...")])
        lines += table(["ID", "Failed check", "Bug type", "Severity", "Evidence"], rows, [5, 28, 16, 8, 34])

    lines += list(extra)
    return result.wasSuccessful(), rate, verdict, lines


def _all_tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _all_tests(item)
        else:
            yield item
