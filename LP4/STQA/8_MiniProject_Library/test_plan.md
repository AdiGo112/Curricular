# Mini Project 8: Library Management System Test Plan and Test Report

## 1. System Environment

| Item | Selection |
| --- | --- |
| Application | Library Management System (console application) |
| Language / Platform | Python 3, any OS (Windows 11 used) |
| Test runner | `unittest` (Python built-in) |
| Coverage tool | `coverage.py` (statement + branch coverage) |
| Files | `library.py` (app), `test_library.py` (tests), `run_tests.py` (runner + report) |

## 2. Test Plan

### 2.1 Objective
Verify the catalogue, membership and circulation rules, including the fine calculation, using black-box and white-box techniques at unit and integration level.

### 2.2 Features to be Tested

| ID | Feature | Rule |
| --- | --- | --- |
| F1 | Add book | ISBN-13 must pass the checksum; title and author required; copies ≥ 1; same ISBN adds copies |
| F2 | Search | By title or author, case-insensitive |
| F3 | Register member | Type is student or faculty; unique ID; name required |
| F4 | Issue book | Student max 3 books for 14 days; faculty max 5 for 30 days; copy must be available; no unpaid fine; no duplicate loan |
| F5 | Return book | Fine is ₹2/day for days 1–7, then ₹5/day, capped at ₹500; faculty pay half |
| F6 | Pay fine | Amount between 1 and the fine due |

### 2.3 Features Not Tested
Persistent storage (data is in memory) and multi-user access.

### 2.4 Approach

| Level | Technique | Test class |
| --- | --- | --- |
| Unit (white-box) | Branch coverage of `valid_isbn13()` and `calculate_fine()` | `WhiteBoxISBN`, `WhiteBoxFine` |
| Unit (black-box) | Equivalence Partitioning (EP), Boundary Value Analysis (BVA) | `BlackBoxCatalogue`, `BlackBoxMembers`, `BlackBoxCirculation` |
| Integration | Catalogue + Members + Circulation working together | `Integration` |
| Coverage | coverage.py, statement + branch | `run_tests.py` |
| Manual | Console menu (section 4.3) | — |

### 2.5 Pass/Fail and Acceptance Criteria
- A test **passes** when the actual result equals the expected result.
- All tests pass and branch coverage ≥ 90% → **ACCEPTED**
- Pass rate ≥ 90% and coverage ≥ 80% → **ACCEPTED WITH MINOR DEFECTS**
- Otherwise → **REJECTED**

## 3. Bug Taxonomy

| Category | Description | Example here |
| --- | --- | --- |
| Logic / Calculation | Wrong formula or branch | Fine charged ₹5 from day 1 |
| Boundary | Off-by-one at a limit | Student allowed a 4th book |
| Validation | Bad input accepted | ISBN with wrong check digit accepted |
| State / Data consistency | Counters out of sync | Available copies not restored on return |
| Error handling | Crash instead of a message | Unknown member raises `KeyError` |
| Test-script defect | Test is wrong, not the app | Wrong expected data in a test |
| Coverage gap | Code no test reaches | Untested error branch |

**Severity:** Critical (crash / data loss) > Major (rule broken) > Minor (message or cosmetic) > Trivial.

## 4. Test Cases with Test Procedures

### 4.1 White-box (unit)

| TC | Function | Path / branch | Input | Expected |
| --- | --- | --- | --- | --- |
| WB1 | `valid_isbn13` | valid path | `978-0-13-468599-1` | True |
| WB2 | `valid_isbn13` | length ≠ 13 | `978013468599` | False |
| WB3 | `valid_isbn13` | non-digit | `97801346859X1` | False |
| WB4 | `valid_isbn13` | checksum fails | `9780134685992` | False |
| WB5 | `calculate_fine` | days ≤ 0 | 0, student | 0 |
| WB6 | `calculate_fine` | 1–7 days | 7, student | 14 |
| WB7 | `calculate_fine` | > 7 days | 8, student | 19 |
| WB8 | `calculate_fine` | cap | 200, student | 500 |
| WB9 | `calculate_fine` | faculty half | 8, faculty | 9 |

### 4.2 Black-box and Integration

| TC | Scenario | Procedure | Expected | Technique |
| --- | --- | --- | --- | --- |
| BB1 | Invalid ISBN | `add_book("1234567890123", …)` | Error | EP |
| BB2 | Zero copies | `add_book(isbn, …, 0)` | Error | BVA |
| BB3 | Blank title | `add_book(isbn, "   ", …)` | Error | EP |
| BB4 | Same ISBN again | Add 2, then add 3 more | copies = 5 | EP |
| BB5 | Search case | Search `"BOOK 5991"` | 1 result | EP |
| BB6 | Invalid member type | Type `visitor` | Error | EP |
| BB7 | Blank name | Name `"  "` | Error | EP |
| BB8 | Duplicate member | Register `S1` twice | Error | EP |
| BB9 | Student due date | Issue on 01-11-2026 | Due 15-11-2026 | — |
| BB10 | Student limit | Issue 3 books, then a 4th | 3rd OK, 4th error | BVA |
| BB11 | No copies | 2 copies, 3 members issue | 3rd error | BVA |
| BB12 | Same book twice | Issue the same ISBN again | Error | EP |
| BB13 | Unknown book | Issue an ISBN not in the catalogue | Error | EP |
| BB14 | Return on due date | Return on the due date | Fine 0 | BVA |
| BB15 | 1 day late | Return due + 1 | Fine 2 | BVA |
| BB16 | Return not issued | Return a book never issued | Error | EP |
| BB17 | Unknown member | Issue to `Z9` | Error | EP |
| IT1 | Fine blocks issue | Issue → return 10 days late → issue again → pay 29 → issue | Fine 29, blocked, then allowed | Integration |
| IT2 | Copies consistent | Issue then return | available 2 → 1 → 2 | Integration |
| IT3 | Overpay | Fine 4, pay 100 | Error | Integration |

### 4.3 Manual: Console Menu (`python library.py`)

| TC | Steps | Expected | Result |
| --- | --- | --- | --- |
| M1 | 2 → `python` | Head First Python listed | Pass |
| M2 | 4 → `S101` → `978-0-596-52068-7` | "Issued. Due date: …" | Pass |
| M3 | 5 → same → late `10` | "Fine: Rs 29" | Pass |
| M4 | 4 → `S101` → another ISBN | "Error: Unpaid fine of Rs 29" | Pass |
| M5 | 6 → `S101` → `29` | "Remaining fine: Rs 0" | Pass |
| M6 | 7 → `S101` | Name, type, 0 books, fine 0 | Pass |
| M7 | `abc` at the menu | "Invalid choice" | Pass |

## 5. Bugs Found During Testing

| ID | Found by | Description | Category | Severity | Status |
| --- | --- | --- | --- | --- | --- |
| BUG-01 | Test run 1 | `test_search_case_insensitive` failed: the test built book titles from the ISBN **with hyphens** (`"99-1"`), so its expected data was wrong | Test-script defect | Minor | Fixed in test |
| BUG-02 | coverage.py, run 1 | Coverage was 64%: no test reached the blank-title, blank-name, unknown-book and duplicate-loan checks | Coverage gap | Major | Fixed: BB3, BB7, BB12, BB13 added |

The console menu (`main()`) is excluded from coverage with `# pragma: no cover`, because it is tested manually (4.3).

## 6. Test Report

Produced by `python run_tests.py`, which writes `test_report.txt` and `htmlcov/index.html`.

| Metric | Result |
| --- | --- |
| Automated test cases | 29 |
| Passed / Failed | 29 / 0 |
| Pass rate | 100% |
| Statement coverage | 93 / 93 |
| Branch coverage | 38 / 38 |
| Manual test cases | 7 / 7 passed |
| **Verdict** | **ACCEPTED** |

## How to Run

```bash
pip install coverage
python library.py        # use the app
python run_tests.py      # tests + coverage + report
```
