# Assignment 8: Mini Project - Library Management System Testing

## Aim
Create a small application. Narrate a concise test plan consisting of features to be tested and a bug taxonomy. Prepare test cases including test procedures. Perform selective black-box and white-box testing covering unit and integration tests with suitable testing tools. Prepare test reports based on pass/fail criteria and judge the acceptance of the application developed.

## Theory and Fundamentals

### Test plan
A test plan says **what** will be tested, **how**, **with which tools** and **when to stop**. Main parts used here: system environment, objective, features to be tested, features not tested, approach, pass/fail and acceptance criteria.

### Bug taxonomy
A taxonomy is a classification of bugs by type and severity. It helps testers decide where to look and helps managers see which kind of bug is common. Types used: logic/calculation, boundary, validation, state/data consistency, error handling, test-script defect, coverage gap.

### Black-box testing
Tests are designed from the **requirements** only, without looking at the code.

- **Equivalence partitioning (EP)**: split inputs into classes that behave alike and test one value from each. Example: member type is `student`, `faculty` or invalid (`visitor`).
- **Boundary value analysis (BVA)**: test values at the edges, where bugs gather. Example: student limit is 3 books, so test the 3rd (allowed) and 4th (refused). Copies = 0 against a minimum of 1.

### White-box testing
Tests are designed from the **code structure**, so that every path runs.

| Coverage | Meaning |
| --- | --- |
| **Statement coverage** | every line runs at least once |
| **Branch (decision) coverage** | every `if` is taken both true and false |
| **Path coverage** | every possible route through the function |

Branch coverage is stronger than statement coverage. 100% of branches also gives 100% of statements.

### Levels of testing
| Level | What is tested | Here |
| --- | --- | --- |
| **Unit** | one function or class in isolation | `valid_isbn13()`, `calculate_fine()` |
| **Integration** | modules working together | catalogue + members + circulation |
| **System** | the whole application | manual menu test |
| **Acceptance** | does it meet the criteria to be accepted | verdict in the report |

### Pass/fail and acceptance criteria
A test **passes** when the actual result equals the expected result. The whole application is judged against fixed rules written *before* testing, so the verdict is not a matter of opinion.

### Test oracle and tools
The expected value is the **oracle**. Tools: `unittest` (Python built-in test framework), `coverage.py` (measures statement and branch coverage).

## How the Code / Document Works

Folder `8_MiniProject_Library/`: `library.py` (application), `test_library.py` (tests), `run_tests.py` (runner and report), `test_plan.md` (plan, cases, bugs, report), plus the generated `test_report.txt` and `htmlcov/`.

### The application (`library.py`)
A console Library Management System with three modules.

| Module | Methods |
| --- | --- |
| Catalogue | `add_book`, `search` |
| Members | `register_member` |
| Circulation | `issue_book`, `return_book`, `pay_fine` |

Business rules (from the file header):
- Student: max 3 books for 14 days. Faculty: max 5 books for 30 days (`LIMITS = {"student": (3, 14), "faculty": (5, 30)}`).
- Fine: Rs 2 per day for the first 7 late days, Rs 5 per day after that, maximum Rs 500 per book. Faculty pay half.
- A member with an unpaid fine cannot issue a new book.
- Errors are raised as `LibraryError`.

**Two pure functions are the main white-box targets.**

```python
def valid_isbn13(isbn):
    digits = isbn.replace("-", "")
    if len(digits) != 13 or not digits.isdigit():
        return False
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits))
    return total % 10 == 0
```

```python
def calculate_fine(days_late, member_type):
    if days_late <= 0:
        return 0
    if days_late <= 7:
        fine = days_late * 2
    else:
        fine = 7 * 2 + (days_late - 7) * 5
    fine = min(fine, FINE_CAP)
    if member_type == "faculty":
        fine //= 2
    return fine
```

For example, 8 days late gives 14 + 5 = 19 for a student and 9 for faculty (integer halving).

`issue_book` checks, in order: unpaid fine, already has this book, limit reached, no copies. Dates are passed in as the `today` argument (default `date.today()`), which makes the code **testable** because tests can use a fixed date.

`main()` is the console menu. It is marked `# pragma: no cover` and is tested manually.

### The tests (`test_library.py`): 29 test cases
| Class | Type | Tests | Technique |
| --- | --- | --- | --- |
| `WhiteBoxISBN` | unit, white-box | 4 | one test per branch: valid, wrong length, non-digit, bad checksum |
| `WhiteBoxFine` | unit, white-box | 5 | `<= 0`, 1 to 7 days, over 7, cap, faculty half |
| `BlackBoxCatalogue` | black-box | 5 | EP and BVA (copies = 0) |
| `BlackBoxMembers` | black-box | 3 | EP (invalid type, blank name, duplicate ID) |
| `BlackBoxCirculation` | black-box | 9 | BVA (3rd and 4th book, no copies, return on due date, 1 day late), EP |
| `Integration` | integration | 3 | multi-module flows |

A white-box test names the branch it covers in its docstring:

```python
def test_cap(self):
    """Branch: min() cap at Rs 500"""
    self.assertEqual(calculate_fine(200, "student"), 500)
```

The main integration test follows a full story: issue, return 10 days late (fine 29), issue is blocked, pay 29, issue is allowed.

```python
fine = self.lib.return_book("S1", ISBN_A, due + timedelta(days=10))
self.assertEqual(fine, 29)
with self.assertRaises(LibraryError):
    self.lib.issue_book("S1", ISBN_B, due + timedelta(days=10))
self.assertEqual(self.lib.pay_fine("S1", 29), 0)
```

`BlackBoxBase.setUp` creates a fresh `Library` with books and members before every test, so the tests are independent.

### Runner and report (`run_tests.py`)
1. Starts `coverage.Coverage(branch=True, ...)` **before** importing `test_library`, so `library.py` is measured.
2. Runs the tests with `unittest`, flattens the suite to get each test case.
3. Calculates pass rate and the coverage percent, then decides the verdict:

```python
if passed == total and percent >= 90:
    verdict = "ACCEPTED"
elif rate >= 90 and percent >= 80:
    verdict = "ACCEPTED WITH MINOR DEFECTS"
else:
    verdict = "REJECTED"
```

4. Writes `test_report.txt` (one row per test with its description, totals, the coverage table, verdict, and a "DEFECT" line for each failure) and `htmlcov/index.html` (green lines executed, red not executed).
5. Exit code is 0 only for ACCEPTED.

### The test plan document (`test_plan.md`)
Sections: 1 System environment, 2 Test plan (objective, features F1 to F6, features not tested: persistent storage and multi-user access, approach table, acceptance criteria), 3 Bug taxonomy with severity (Critical > Major > Minor > Trivial), 4 Test cases with procedures (WB1 to WB9, BB1 to BB17, IT1 to IT3, and 7 manual menu cases M1 to M7), 5 Bugs found, 6 Test report.

Bugs it records:

| ID | Description | Category |
| --- | --- | --- |
| BUG-01 | a test built book titles from the ISBN with hyphens, so its expected data was wrong | Test-script defect, fixed in the test |
| BUG-02 | first coverage run was 64% because no test reached blank title, blank name, unknown book and duplicate loan checks | Coverage gap, fixed by adding BB3, BB7, BB12, BB13 |

## How to Run and Expected Output

```bash
pip install coverage
python library.py        # use the console application
python run_tests.py      # tests + coverage + report
python -m unittest -v test_library   # tests only
```

Expected final lines of `python run_tests.py`:

```
Coverage: 100.0%   Verdict: ACCEPTED
Reports: test_report.txt, htmlcov/index.html
```

`test_report.txt` shows:

```
Total: 29   Passed: 29   Failed: 0   Pass rate: 100.0%
library.py      93      0     38      0   100%
Verdict: ACCEPTED
```

That is 93 statements and 38 branches, with none missed. Open `htmlcov/index.html` in a browser to see which lines ran.

The manual menu tests (M1 to M7) are done by running `python library.py`, for example choose 5, enter the member and ISBN, and `10` days late. The app prints `Fine: Rs 29`.

## Related Concepts and Real-World Tools

- **Frameworks**: pytest, JUnit, TestNG, NUnit. `pytest-cov`, JaCoCo (Java) and Istanbul/nyc (JavaScript) measure coverage.
- **Mocking**: `unittest.mock`, Mockito, to isolate a unit from its dependencies.
- **Mutation testing**: tools such as mutmut and PIT change the code to check whether tests notice. This shows that high coverage does not always mean good tests.
- **Static analysis**: pylint, flake8, SonarQube find problems without running the code.
- **CI**: run the tests and enforce a coverage gate (for example fail below 90%) on every commit.
- **Test management**: TestRail, Zephyr, JIRA for plans and bugs.
- **Property-based testing**: Hypothesis generates many inputs automatically.

## Viva Questions

1. **What is a test plan? What did yours contain?**
   A document defining scope, approach, tools and criteria for testing. Mine has environment, features to test and not test, approach, bug taxonomy, test cases, and acceptance criteria.

2. **Difference between black-box and white-box testing?**
   Black-box uses only requirements and checks inputs and outputs. White-box uses knowledge of the code and aims to execute every statement or branch.

3. **What is boundary value analysis? Give an example from your project.**
   Testing at the edges of a range. A student may borrow 3 books, so I test the 3rd (allowed) and the 4th (refused). Also copies = 0 and a return exactly on the due date.

4. **What is equivalence partitioning?**
   Dividing inputs into classes where the system behaves the same, and testing one value per class. Example: member type `student`, `faculty`, or invalid like `visitor`.

5. **Difference between statement coverage and branch coverage?**
   Statement coverage means every line runs. Branch coverage means every decision outcome (true and false) runs. Branch coverage is stronger.

6. **Which tools did you use?**
   `unittest` as the test framework and `coverage.py` for statement and branch coverage, with an HTML report.

7. **What is the difference between unit and integration testing here?**
   Unit tests check `valid_isbn13()` and `calculate_fine()` alone. Integration tests check issue, late return, fine blocking and payment working together.

8. **How is the acceptance verdict decided?**
   All tests pass and coverage is at least 90% gives ACCEPTED. Pass rate at least 90% and coverage at least 80% gives ACCEPTED WITH MINOR DEFECTS. Otherwise REJECTED.

9. **Why is `main()` excluded from coverage?**
   It is an interactive menu waiting for keyboard input, so it is tested manually (cases M1 to M7) and marked `# pragma: no cover`.

10. **Does 100% coverage mean there are no bugs?**
    No. It only shows that every line and branch ran. Tests can still miss wrong expected values or missing requirements. The project's own BUG-01 was a wrong test, not wrong code.
