# Assignment 9: Mini Project - TaskTrack with Selenium Regression Testing

## Aim
Create a small web-based application. Narrate a concise test plan consisting of features to be tested and a bug taxonomy. Narrate scripts in order to perform regression tests. Identify the bugs using Selenium WebDriver and IDE and generate test reports encompassing exploratory testing.

## Theory and Fundamentals

### Types of testing used
| Type | Meaning | In this project |
| --- | --- | --- |
| **System testing** | the whole app in a real environment | Selenium in a browser |
| **Regression testing** | re-run old tests after every change to confirm nothing that worked is now broken | WebDriver `test_selenium_regression.py`, IDE `TaskTrack.side` |
| **Exploratory testing** | testers learn, design and run tests at the same time, without fixed scripts | 20-minute charter on each build (`exploratory_log.csv`) |
| **Acceptance testing** | decide if the app can be accepted | verdict in the report |

### Regression testing
Every bug fix or new feature may break something else. A **regression suite** is a stable set of tests that is run again and again, so it is a good candidate for automation. It should be fast, repeatable and independent.

### How regression finds bugs here: two builds
The same code has two builds. **v1.0** (`python app.py 1.0`) is the first release and has 6 bugs, one of each bug type. **v1.1** (`python app.py`) is the fixed release. The *same* regression scripts run on both builds:
- v1.0: scripts fail, so the bugs are identified, and the verdict is REJECTED.
- v1.1: all scripts pass, which shows the bugs are fixed and nothing else broke. The verdict is ACCEPTED.

### Exploratory testing
It has a **charter** (a goal and a time box), is based on the tester's experience and curiosity, and notes what was tried and what was seen. It finds bugs that scripted tests miss, for example odd inputs and strange navigation. A bug found this way is then added to the regression suite, so it can never come back unnoticed.

### Selenium basics needed
- **WebDriver**: a script controls a real browser. **Locators** (ID, CSS, XPath) find elements. **Waits** handle page loading.
- **Selenium IDE**: a browser extension that **records** your clicks and typing as a test and plays it back. Saved as a `.side` file (JSON). Good for quick tests and for non-programmers.
- **assert vs verify (IDE)**: `assert…` stops the test at the first failure. `verify…` logs the failure and continues.
- **Stale element**: a reference to a page element that no longer exists because the page reloaded (`StaleElementReferenceException`).
- **Flaky test**: a test that sometimes passes and sometimes fails without any code change, often because of timing.

### Bug taxonomy
Bugs are classified by **type** and **severity**.

| Type | Example in TaskTrack |
| --- | --- |
| Functional | "Done" does nothing |
| Validation / Input | password without a digit accepted |
| UI / Cosmetic | heading reads "My Task" |
| Security | HTML in a task title runs (XSS) |
| Session / State | still logged in after logout |
| Crash / Exception | HTTP 500 on an invalid task index |
| Automation / Test | stale element in a Selenium script |

Severity: Critical (crash, data loss or security hole), Major (main feature broken), Minor (small defect), Trivial (cosmetic).

## How the Code / Document Works

Folder `9_MiniProject_TestIntegration/` contains:

| File | PS part |
| --- | --- |
| `app.py` | the web application (two builds) |
| `test_plan.md` | test plan, features, bug taxonomy, bugs, exploratory, summary |
| `test_selenium_regression.py` | regression scripts in Selenium WebDriver (RT-01 to RT-12) |
| `TaskTrack.side` | regression scripts in Selenium IDE (IDE-1 to IDE-4) |
| `exploratory_log.csv` | notes from the exploratory session |
| `report.py` | writes the test report |
| `test_report_selenium.txt` | generated test report (accepted build v1.1) |

### The application (`app.py`)
A small Flask app, with storage in memory. Rules: username `[A-Za-z0-9_]{3,15}`; password at least 6 characters with a digit; task title 1 to 50 characters.

| Route | Behaviour |
| --- | --- |
| `/` | go to tasks if logged in, else to login |
| `/register`, `/login` | forms with validation messages |
| `/logout` | ends the session |
| `/tasks`, `/tasks/add` | list and add tasks (login needed) |
| `/tasks/<i>/done`, `/tasks/<i>/delete` | complete or delete; a bad index is ignored |

**Build switch:** `VERSION = "1.1"` and `buggy()` returns `VERSION == "1.0"`. Each planted bug is one guarded line:

```python
if not buggy():   # BUG-04 (v1.0): logout does not end the session
    session.pop("user", None)
```

| Bug | What v1.0 does | Type, severity |
| --- | --- | --- |
| BUG-01 | skips the digit rule in `validate_password` | Validation/Input, Major |
| BUG-02 | shows the heading "My Task" | UI/Cosmetic, Trivial |
| BUG-03 | "Done" does nothing | Functional, Major |
| BUG-04 | logout keeps the session | Session/State, Critical |
| BUG-05 | no range check, so `/tasks/99/delete` raises IndexError (HTTP 500) | Crash/Exception, Critical |
| BUG-06 | renders the title with `\|safe` (XSS) | Security, Critical |

**Test-friendly HTML:** fixed ids (`username`, `password`, `confirm`, `submit`, `heading`, `error`, `msg`, `task-title`, `add-task`, `task-list`, `count`, `logout`, `version`) are the locators used by WebDriver and IDE. The footer shows `TaskTrack v1.0` or `TaskTrack v1.1`.

### Selenium WebDriver regression (`test_selenium_regression.py`)
- `python test_selenium_regression.py 1.0` tests the buggy build and prints the report, with the bugs identified, to the console. With no argument it tests v1.1 and writes `test_report_selenium.txt`, so the file always holds the accepted build. The script sets `webapp.VERSION`, starts the app on port 5001 in a thread (`make_server`) and opens Chrome. `BROWSER=edge` and `HEADLESS=1` are optional.
- `setUp` clears users, tasks and cookies, so every script is independent.
- 12 scripts, RT-01 to RT-12. Each docstring ends with the bug type and severity reported if it fails:

```python
def test_11_invalid_task_index(self):
    """RT-11: Invalid task index in the URL does not crash [Crash/Exception, Critical]"""
    self.register_and_login()
    self.driver.get(BASE + "/tasks/99/delete")
    self.assertNotIn("Internal Server Error", self.driver.page_source)
```

- **`click_and_wait`:** `click()` returns before the next page loads, so the helper waits until the old `<html>` element goes stale. This fixed BUG-07, a `StaleElementReferenceException` in the script itself (an Automation/Test bug).

### Selenium IDE (`TaskTrack.side`)
The suite **Regression** has 4 recorded tests: IDE-1 register, login, add, logout (after which `/tasks` must show Login); IDE-2 invalid login; IDE-3 password without a digit; IDE-4 Done, HTML title, invalid index.

```json
{ "command": "verifyText", "target": "css=#task-list .title", "value": "<b>hi</b>" }
```

On v1.0, IDE-1, IDE-3 and IDE-4 fail, and together they catch all 6 bugs. On v1.1 all 4 pass.

### Report (`report.py`) and exploratory testing
`run_and_report(classes, title, extra)` runs the suite once. A `TimedResult` class records how many seconds each test took. The function returns the report as plain-text grid tables (built by `table()`, which wraps long cells):

| Section | Table columns |
| --- | --- |
| Header | Application, Build, Tool, Browser, Date (with seconds) |
| 1. Summary | Total, Passed, Failed, Pass rate, Duration (s), Verdict |
| 2. Test Results | ID, Test case, Bug type if it fails, Severity, Time (s), Result |
| 3. Bugs Identified | ID, Failed check, Bug type, Severity, Evidence (the assertion error) |
| 4. Exploratory Testing | ID, Area, What was tried, What was observed, Result, Bug (rows of `exploratory_log.csv` for that build) |

The bug type and severity come from the test's docstring, `"RT-03: ... [Validation/Input, Major]"`. Verdict: 100% is ACCEPTED, at least 90% is ACCEPTED WITH MINOR DEFECTS, anything lower is REJECTED.

On v1.0, exploration found BUG-06 (XSS), which no script covered at the time, so it was added as RT-12. On v1.1 it found BUG-08: Done and Delete are GET links, so a prefetch could change data. BUG-08 is Minor and still open.

### Results

| Build | WebDriver | IDE | Exploratory | Verdict |
| --- | --- | --- | --- | --- |
| v1.0 | 6/12 (50%) | 1/4 | 4 bugs | REJECTED |
| v1.1 | 12/12 (100%) | 4/4 | 1 Minor (BUG-08) | ACCEPTED |

## How to Run and Expected Output

```bash
pip install -r ../requirements.txt      # selenium, flask, ...
cd 9_MiniProject_TestIntegration
python test_selenium_regression.py 1.0   # console: v1.0 REJECTED, 6 bugs identified
python test_selenium_regression.py       # test_report_selenium.txt: v1.1 ACCEPTED
```

An excerpt from the v1.0 console output:
```
3. Bugs Identified
+-------+------------------------------+------------------+----------+------------------------------------+
| ID    | Failed check                 | Bug type         | Severity | Evidence                           |
+=======+==============================+==================+==========+====================================+
| RT-05 | Valid login opens My Tasks   | UI/Cosmetic      | Trivial  | AssertionError: 'My Task' != 'My   |
|       | page                         |                  |          | Tasks'                             |
+-------+------------------------------+------------------+----------+------------------------------------+
...
```

**Selenium IDE:** run `python app.py 1.0` (or `python app.py` for v1.1). In the Selenium IDE extension, choose **Open an existing project** → `TaskTrack.side` → **Run all**. Restart `app.py` before running again, because users are kept in memory.

With Docker (from `STQA`): `docker compose up --build -d tasktrack` serves v1.1 at `http://localhost:5000`.

## Related Concepts and Real-World Tools

- **Frameworks**: pytest, JUnit/TestNG with Selenium. Page Object Model for maintainable scripts.
- **Modern UI automation**: Cypress, Playwright (auto-waiting reduces flaky tests).
- **Visual and cross-browser**: BrowserStack, Sauce Labs, Percy.
- **Selenium Grid** runs the regression suite on many browsers in parallel (Assignment 5).
- **CI**: Jenkins and GitHub Actions run the regression suite on every commit, so regressions are found at once.
- **Bug tracking**: JIRA, Bugzilla (Assignment 4).
- **Exploratory tools**: session-based test management, screen recorders, browser DevTools.
- **Web security**: output escaping against XSS (BUG-06), POST plus CSRF tokens for state changes (BUG-08), OWASP ZAP.

## Viva Questions

1. **What is regression testing and why automate it?**
   Re-running earlier tests after a change to confirm nothing broke. It is repeated often, so automation saves time and is more reliable.

2. **How did your regression suite identify bugs?**
   The same 12 WebDriver scripts and 4 IDE tests ran on v1.0 and v1.1. On v1.0, 6 scripts failed, and each failure maps to one bug through the type and severity in its docstring. On v1.1 all passed, which proves the fixes work and nothing else broke.

3. **What is exploratory testing and how is it different from scripted testing?**
   The tester learns, designs and executes tests at the same time within a time-boxed charter. Scripted testing follows pre-written cases. Here, exploration found the XSS bug (BUG-06), which was then scripted as RT-12.

4. **Difference between Selenium IDE and WebDriver?**
   IDE is record and playback with little coding. WebDriver is a programming API (Python here), which is more flexible and supports loops, conditions and frameworks.

5. **Difference between assert and verify in Selenium IDE?**
   `assert` stops the test at the first failure. `verify` logs the failure and continues, so one run of IDE-4 reports three bugs.

6. **What is a stale element exception and how did you handle it?**
   It occurs when a stored element no longer exists because the page reloaded. The `click_and_wait` helper waits until the old page goes stale before reading the new page (BUG-07).

7. **What is the bug taxonomy of your project?**
   Functional, validation, UI, security, session/state, crash and automation/test defects, each with a severity of Critical, Major, Minor or Trivial. v1.0 has one bug of each app type.

8. **Why is BUG-06 (XSS) Critical?**
   A task title containing a script would run in the browser, so an attacker could steal the session. Jinja escapes output by default. v1.0 turned this off with `|safe`.

9. **What is the open bug BUG-08?**
   Done and Delete use GET links, so visiting a URL changes data. It is Minor and accepted for the lab version. The fix is POST forms with CSRF tokens.

10. **How is the acceptance decision made?**
    By pass rate: 100% is ACCEPTED, at least 90% with only minor bugs open is ACCEPTED WITH MINOR DEFECTS, below 90% is REJECTED. v1.0 is rejected (50%). v1.1 is accepted (100%, with only BUG-08, a Minor bug, open).
