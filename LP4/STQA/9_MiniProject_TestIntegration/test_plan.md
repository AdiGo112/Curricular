# Mini Project: TaskTrack Test Plan and Test Report

## 1. System Environment

| Item | Selection |
| --- | --- |
| Application | TaskTrack, a small web-based to-do list app |
| Language | Python 3 |
| Framework | Flask (web server and HTML templates) |
| Storage | In-memory Python dictionaries |
| Browsers | Google Chrome, Microsoft Edge |
| Automation tools | Selenium WebDriver (Python), Selenium IDE (browser extension) |
| Unit test tool | `unittest` (Python built-in) |
| OS | Windows 11 (works on Linux/macOS also) |

## 2. Test Plan

### 2.1 Objective
Verify that a user can register, log in, manage tasks and log out correctly, and that invalid input is rejected with a clear message.

### 2.2 Scope: Features to be Tested

| ID | Feature | Description |
| --- | --- | --- |
| F1 | Registration | Username 3–15 chars (letters, digits, `_`), password ≥ 6 chars with a digit, confirm password, unique username |
| F2 | Login | Valid credentials open the task page, invalid ones show an error |
| F3 | Add task | Title 1–50 characters, blank titles rejected |
| F4 | Complete task | "Done" link strikes through the task |
| F5 | Delete task | "Delete" link removes the task |
| F6 | Logout / session | Logout ends the session, `/tasks` is protected |

### 2.3 Features Not Tested
Persistent storage, password reset, performance and load testing (outside lab scope).

### 2.4 Approach

| Level | Technique | File |
| --- | --- | --- |
| Unit (white-box) | Branch coverage of `validate_username`, `validate_password`, `validate_task` | `test_unit_integration.py` |
| Unit (black-box) | Equivalence partitioning and boundary value analysis through HTTP | `test_unit_integration.py` |
| Integration | Full flow: register → login → add → done → delete → logout | `test_unit_integration.py` |
| System / Regression | Selenium WebDriver in a real browser | `test_selenium_regression.py` |
| Record & playback | Selenium IDE project | `TaskTrack.side` |
| Exploratory | Time-boxed manual session (section 5) | — |

### 2.5 Entry and Exit Criteria
- **Entry:** the app starts without errors and all pages load.
- **Exit:** every planned test has run and there are no open Critical or Major bugs.

### 2.6 Pass/Fail and Acceptance Criteria
- A test **passes** when the actual result equals the expected result.
- Pass rate 100% → **ACCEPTED**
- Pass rate ≥ 90%, and only Minor/Trivial bugs open → **ACCEPTED WITH MINOR DEFECTS**
- Otherwise → **REJECTED**

### 2.7 Deliverables
Test plan (this file), test scripts, generated test reports (`test_report_unit.txt`, `test_report_selenium.txt`), bug list.

## 3. Bug Taxonomy

Each bug is classified by **type** and by **severity**.

| Type | Meaning | Example in this app |
| --- | --- | --- |
| Functional | Feature does not do what is required | Task not added to list |
| Validation / Input | Wrong input accepted or right input rejected | Blank task title accepted |
| UI / Cosmetic | Layout, text or style issue | Error message not shown in red |
| Security | Unauthorised access possible | `/tasks` opens without login |
| Session / State | Wrong behaviour across requests | User still logged in after logout |
| Crash / Exception | Server error (HTTP 500) | Error page on invalid task index |
| Automation / Test | Defect in the test script, not the app | Stale element in Selenium script |

| Severity | Meaning |
| --- | --- |
| Critical | App crashes or data is lost; no workaround |
| Major | Main feature broken; workaround is hard |
| Minor | Feature works but with a small defect |
| Trivial | Cosmetic issue |

## 4. Test Cases with Test Procedures

| TC ID | Scenario | Test Procedure (Steps) | Test Data | Expected Result | Type |
| --- | --- | --- | --- | --- | --- |
| TC01 | Open app | 1. Open `http://127.0.0.1:5000` | — | Redirects to Login page | Black-box |
| TC02 | Valid registration | 1. Open Register 2. Enter data 3. Click Register | `abc` / `pass12` / `pass12` | "Registration successful" | BVA (min) |
| TC03 | Username max length | Same as TC02 | 15 × `a` | Registration successful | BVA (max) |
| TC04 | Username too long | Same as TC02 | 16 × `a` | Error "3-15 letters…" | BVA (max+1) |
| TC05 | Password without digit | Same as TC02 | `abcdefg` | Error "must contain a digit" | EP |
| TC06 | Password mismatch | Same as TC02 | `pass12` / `other12` | Error "Passwords do not match" | EP |
| TC07 | Duplicate username | Register `tester`, then `TESTER` | — | Error "Username already exists" | EP |
| TC08 | Empty login | 1. Open Login 2. Click Login | blank | Error "Enter username and password" | EP |
| TC09 | Wrong password | Login with a registered user | `tester` / `wrong12` | Error "Invalid username or password" | EP |
| TC10 | Valid login | Login with a registered user | `tester` / `pass12` | "My Tasks" page with username | Black-box |
| TC11 | Add task | Type a title, click Add | `Write SRS` | Task listed, count = 1 | Black-box |
| TC12 | Blank task | Type spaces, click Add | `"   "` | Error "cannot be empty" | Black-box |
| TC13 | Complete task | Click Done | — | Task struck through | Black-box |
| TC14 | Delete task | Click Delete | — | Task removed, count = 0 | Black-box |
| TC15 | Invalid task index | Open `/tasks/99/delete` | — | No crash, redirect to tasks | Robustness |
| TC16 | Protected page | Open `/tasks` without login | — | Redirect to Login | Security |
| TC17 | Logout | Click Logout, then open `/tasks` | — | Login page shown | Security |

## 5. Regression Scripts

Regression testing re-runs the same tests after every code change to confirm nothing that worked before is now broken.

1. **Selenium WebDriver** (`test_selenium_regression.py`, 10 scripts RT-01 to RT-10)
   - The script starts the app on port 5001, opens Chrome, and repeats the flows in section 4.
   - Run it after every change with `python test_selenium_regression.py`. It writes `test_report_selenium.txt`.
2. **Selenium IDE** (`TaskTrack.side`)
   - Install the Selenium IDE extension in Chrome or Edge, then choose **Open an existing project** → `TaskTrack.side`.
   - Start `python app.py`, then click **Run all tests** in the *Regression* suite.
   - The users are stored in memory, so restart `app.py` before running it again. Otherwise "ideuser" already exists.

## 6. Bugs Identified

These bugs were found while building and testing this project.

| Bug ID | Found by | Description | Type | Severity | Status |
| --- | --- | --- | --- | --- | --- |
| BUG-01 | Unit/Integration tests | Every error message crashed the server with `TypeError: got multiple values for keyword argument 'error'` (HTTP 500) | Crash / Exception | Critical | Fixed: merged the defaults in `page()` |
| BUG-02 | Selenium regression | Logging in right after registering failed with `StaleElementReferenceException`, because the script typed into the old page before it reloaded | Automation / Test | Major | Fixed: open `/login` before typing |
| BUG-03 | Exploratory | "Done" and "Delete" use GET links, so a page prefetch could change data | Security | Minor | Open: accepted for the lab version |

## 7. Exploratory Testing

**Charter:** explore the Register and Task pages for 20 minutes, trying unusual input, to find validation and session problems.

| # | What was tried | Observation | Result |
| --- | --- | --- | --- |
| 1 | Username with spaces `adi go` | Rejected with a clear message | Pass |
| 2 | Same username in different case | Rejected as "already exists" | Pass |
| 3 | Task title of exactly 50 and 51 characters | 50 accepted, 51 rejected | Pass |
| 4 | Task with HTML `<b>hi</b>` | Shown as plain text (Jinja escapes it, so no XSS) | Pass |
| 5 | Browser Back button after logout | The cached page shows, but every action redirects to Login | Pass |
| 6 | Edited URL `/tasks/-1/delete` | 404, no data changed | Pass |
| 7 | Opened `/tasks/0/done` in a second tab | Works on the same session | Pass |

## 8. Test Report Summary

| Suite | Total | Passed | Failed | Pass rate | Verdict |
| --- | --- | --- | --- | --- | --- |
| Unit + Integration (`test_report_unit.txt`) | 19 | 19 | 0 | 100% | ACCEPTED |
| Selenium regression (`test_report_selenium.txt`) | 10 | 10 | 0 | 100% | ACCEPTED |
| Exploratory | 7 | 7 | 0 | 100% | ACCEPTED |

**Conclusion:** all planned tests pass, and the only open bug (BUG-03) is Minor. **The application is accepted.**

## How to Run

```bash
pip install -r ../requirements.txt
python app.py                         # use the app at http://127.0.0.1:5000
python test_unit_integration.py       # white-box, black-box, integration tests
python test_selenium_regression.py    # browser regression (set HEADLESS=1 to hide the window)
```
