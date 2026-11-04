# Mini Project 9: TaskTrack Test Plan and Test Report

> **PS:** Create a small web-based application by selecting relevant system environment / platform and programming languages. Narrate a concise test plan consisting of features to be tested and a bug taxonomy. Narrate scripts to perform regression tests. Identify the bugs using Selenium WebDriver and IDE and generate test reports encompassing exploratory testing.

| PS requirement | Where |
| --- | --- |
| Small web application + environment | `app.py`, section 1 |
| Concise test plan: features to be tested | section 2 |
| Bug taxonomy | section 3 |
| Regression test scripts | `test_selenium_regression.py` (WebDriver), `TaskTrack.side` (IDE), section 4 |
| Bugs identified with WebDriver and IDE | section 5 |
| Test reports with exploratory testing | `test_report_selenium.txt` (accepted build v1.1), `exploratory_log.csv`, sections 6–7 |

## 1. Application and Environment

**TaskTrack** is a small to-do web app: register, log in, add tasks, mark them done, delete them, and log out.

| Item | Selection |
| --- | --- |
| Language / framework | Python 3, Flask (HTML templates) |
| Storage | In-memory dictionaries (reset on restart) |
| Browsers | Google Chrome, Microsoft Edge |
| Test tools | Selenium WebDriver (Python), Selenium IDE (browser extension) |
| OS | Windows 11 (also runs on Linux and macOS) |

There are two builds of the same code, so that regression testing has something to find:

| Build | Run | Meaning |
| --- | --- | --- |
| **v1.0** | `python app.py 1.0` | First release with 6 bugs (marked `BUG-0x (v1.0)` in `app.py`) |
| **v1.1** | `python app.py` | Fixed release |

The page footer shows the build under test (`TaskTrack v1.0` or `v1.1`).

## 2. Test Plan

**Objective:** confirm that every feature works in a real browser, find bugs in v1.0, and confirm that v1.1 fixes them without breaking anything else.

### Features to be tested

| ID | Feature | Rule | Scripts |
| --- | --- | --- | --- |
| F1 | Registration | Username 3–15 letters, digits or `_`; password ≥ 6 chars with a digit; passwords match | RT-02, RT-03, IDE-1, IDE-3 |
| F2 | Login | Valid login opens "My Tasks"; wrong login shows an error | RT-01, RT-04, RT-05, IDE-1, IDE-2 |
| F3 | Add task | Title 1–50 chars; blank rejected; HTML shown as text | RT-06, RT-07, RT-12, IDE-1, IDE-4 |
| F4 | Complete task | "Done" strikes the task through | RT-08, IDE-4 |
| F5 | Delete task | "Delete" removes the task; a bad index does not crash | RT-09, RT-11, IDE-4 |
| F6 | Logout / session | Logout ends the session; `/tasks` needs a login | RT-10, IDE-1 |

**Not tested:** persistent storage, password reset, performance and load.

**Approach:** automated regression with Selenium WebDriver (12 scripts) and Selenium IDE (4 recorded tests), both run on v1.0 and on v1.1. This is followed by a 20-minute manual exploratory session on each build.

**Entry criteria:** the app starts and the login page loads. **Exit criteria:** every script has run and no Critical or Major bug is open.

**Pass/fail and acceptance:** a script passes when the actual result equals the expected result. A 100% pass rate is **ACCEPTED**. A rate of at least 90% is **ACCEPTED WITH MINOR DEFECTS**. Anything lower is **REJECTED**.

## 3. Bug Taxonomy

| Type | Meaning | Example in TaskTrack |
| --- | --- | --- |
| Functional | A feature does not do what is required | "Done" does nothing |
| Validation / Input | Wrong input is accepted or right input is rejected | Password without a digit accepted |
| UI / Cosmetic | Wrong text, layout or style | Heading reads "My Task" |
| Security | Data or pages exposed, or code injection possible | HTML in a task title runs (XSS) |
| Session / State | Wrong behaviour across requests | Still logged in after logout |
| Crash / Exception | Server error (HTTP 500) | Invalid task index crashes |
| Automation / Test | Defect in the test script, not the app | Stale element in a Selenium script |

| Severity | Meaning |
| --- | --- |
| Critical | Crash, data loss or security hole; no workaround |
| Major | A main feature is broken |
| Minor | Small defect; a workaround exists |
| Trivial | Cosmetic only |

## 4. Regression Test Scripts

Regression testing runs the same scripts again after every change, to confirm that the fixes work and that nothing which worked before is now broken.

### 4.1 Selenium WebDriver: `test_selenium_regression.py`

The script starts the app by itself on port 5001, opens Chrome (or Edge), and runs:

| Script | Steps | Expected result | Bug type if it fails |
| --- | --- | --- | --- |
| RT-01 | Open `/` | Login page | Functional, Major |
| RT-02 | Register `seluser` / `pass12` / `pass12` | "Registration successful" | Functional, Critical |
| RT-03 | Register with password `abcdefg` | Error "must contain a digit" | Validation/Input, Major |
| RT-04 | Login `nobody` / `wrong12` | Error "Invalid username or password" | Security, Critical |
| RT-05 | Register and log in | Heading "My Tasks", username shown | UI/Cosmetic, Trivial |
| RT-06 | Add task "Prepare test plan" | Task listed, "1 task(s)" | Functional, Major |
| RT-07 | Add task "   " | Error "cannot be empty" | Validation/Input, Minor |
| RT-08 | Add a task, click Done | Task has class `done` (struck through) | Functional, Major |
| RT-09 | Add a task, click Delete | "0 task(s)" | Functional, Major |
| RT-10 | Logout, then open `/tasks` | Login page | Session/State, Critical |
| RT-11 | Open `/tasks/99/delete` | No HTTP 500; task list shown | Crash/Exception, Critical |
| RT-12 | Add task `<b>hi</b>` | Title shown as the text `<b>hi</b>` | Security, Critical |

### 4.2 Selenium IDE: `TaskTrack.side` (suite "Regression")

| Test | Covers | Key checks |
| --- | --- | --- |
| IDE-1 Register, login, add task, logout | F1, F2, F3, F6 | `verifyText heading = My Tasks`, `assertText heading = Login` after logout |
| IDE-2 Invalid login shows error | F2 | `assertText error` |
| IDE-3 Password without digit rejected | F1 | `assertElementPresent id=error` |
| IDE-4 Done, HTML title, invalid index | F3, F4, F5 | `verifyText title = <b>hi</b>`, `verifyElementPresent li.done`, `assertElementPresent id=count` after `/tasks/99/delete` |

`verify…` commands log a failure and continue, so a single run reports every bug. `assert…` commands stop the test.

## 5. Bugs Identified

| Bug ID | Description | Type | Severity | Found by | Status |
| --- | --- | --- | --- | --- | --- |
| BUG-01 | Password without a digit is accepted | Validation/Input | Major | WebDriver RT-03, IDE-3 | Fixed in v1.1 |
| BUG-02 | Task page heading reads "My Task" | UI/Cosmetic | Trivial | WebDriver RT-05, IDE-1 | Fixed in v1.1 |
| BUG-03 | "Done" link does not mark the task done | Functional | Major | WebDriver RT-08, IDE-4, exploratory ET-04 | Fixed in v1.1 |
| BUG-04 | Logout does not end the session | Session/State | Critical | WebDriver RT-10, IDE-1, exploratory ET-03 | Fixed in v1.1 |
| BUG-05 | `/tasks/99/delete` crashes (IndexError, HTTP 500) | Crash/Exception | Critical | WebDriver RT-11, IDE-4, exploratory ET-02 | Fixed in v1.1 |
| BUG-06 | HTML in a task title is rendered (XSS) | Security | Critical | Exploratory ET-01, then scripted as RT-12 and IDE-4 | Fixed in v1.1 |
| BUG-07 | Script typed into the old page right after a click (`StaleElementReferenceException`) | Automation/Test | Major | WebDriver, while the scripts were being written | Fixed: `click_and_wait()` waits for the new page |
| BUG-08 | Done and Delete are GET links, so a prefetch could change data | Security | Minor | Exploratory ET-07 (v1.1) | Open, accepted for the lab |

## 6. Exploratory Testing

**Charter:** explore Register, Tasks and Logout for 20 minutes on each build, using unusual input and navigation (odd characters, HTML, edited URLs, Back button, case changes).

The session notes are kept in `exploratory_log.csv` (version, id, area, what was tried, what was observed, result, bug). The WebDriver script copies the rows for the build under test into its test report. On v1.0, exploration found BUG-06 (XSS), which no script covered at the time, so it was added to the regression suite as RT-12. This is how exploratory testing feeds regression testing.

## 7. Test Report Summary

| Build | Suite | Total | Passed | Failed | Pass rate | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| v1.0 | WebDriver (console run) | 12 | 6 | 6 | 50% | REJECTED |
| v1.0 | Selenium IDE | 4 | 1 | 3 | 25% | REJECTED |
| v1.0 | Exploratory | 5 | 1 | 4 | — | 4 bugs |
| v1.1 | WebDriver (`test_report_selenium.txt`) | 12 | 12 | 0 | 100% | ACCEPTED |
| v1.1 | Selenium IDE | 4 | 4 | 0 | 100% | ACCEPTED |
| v1.1 | Exploratory | 7 | 6 | 1 | — | 1 Minor bug (BUG-08) |

**Conclusion:** v1.0 is rejected because of 6 bugs (4 Critical). v1.1 fixes all of them, and the same regression scripts show that nothing else broke. Only BUG-08 (Minor) is still open, so **v1.1 is accepted**.

## How to Run

```bash
pip install -r ../requirements.txt

# Selenium WebDriver (starts the app itself; set HEADLESS=1 to hide the browser)
python test_selenium_regression.py 1.0   # buggy build -> 6 bugs identified, printed to the console
python test_selenium_regression.py       # fixed build -> test_report_selenium.txt, ACCEPTED

# Selenium IDE
python app.py 1.0        # or: python app.py   (v1.1)
#   Selenium IDE extension -> Open an existing project -> TaskTrack.side -> Run all (suite "Regression")
#   Restart app.py before running again (users are kept in memory)
```
