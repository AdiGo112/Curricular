# Assignment 9: Mini Project - TaskTrack with Selenium Regression Testing

## Aim
Create a small web-based application. Narrate a concise test plan consisting of features to be tested and a bug taxonomy. Narrate scripts in order to perform regression tests. Identify the bugs using Selenium WebDriver and IDE and generate test reports encompassing exploratory testing.

## Theory and Fundamentals

### Levels and types of testing used
| Type | Meaning | In this project |
| --- | --- | --- |
| **Unit testing** | one function alone | `validate_username`, `validate_password`, `validate_task` |
| **Integration testing** | modules together | register -> login -> add -> done -> delete -> logout |
| **System testing** | the whole app in a real environment | Selenium in a browser |
| **Regression testing** | re-run old tests after every change to confirm nothing that worked is now broken | `test_selenium_regression.py` |
| **Exploratory testing** | testers learn, design and run tests at the same time, without fixed scripts | 20-minute charter (see below) |
| **Acceptance testing** | decide if the app can be accepted | verdict in the report |

### Regression testing
Every bug fix or new feature may break something else. A **regression suite** is a stable set of tests that is run again and again, so it is a good candidate for automation. It should be fast, repeatable and independent.

### Exploratory testing
It has a **charter** (a goal and a time box), is based on the tester's experience and curiosity, and notes what was tried and what was seen. It finds bugs that scripted tests miss, for example odd inputs and strange navigation.

### Black-box and white-box techniques
- **White-box**: tests written by reading the code, so each branch of a validator runs.
- **Black-box**: tests send HTTP requests and check only the response. Uses **EP** (equivalence classes) and **BVA** (boundary values such as username length 3, 15, 16).

### Selenium basics needed
- **WebDriver**: a script controls a real browser. **Locators** (ID, CSS, XPath) find elements. **Waits** handle page loading.
- **Selenium IDE**: a browser extension that **records** your clicks and typing as a test and plays it back. Saved as a `.side` file (JSON). Good for quick tests and for non-programmers.
- **Stale element**: a reference to a page element that no longer exists because the page reloaded (`StaleElementReferenceException`).
- **Flaky test**: a test that sometimes passes and sometimes fails without any code change, often because of timing.

### Bug taxonomy
Bugs are classified by **type** and **severity**.

| Type | Example in TaskTrack |
| --- | --- |
| Functional | task not added to the list |
| Validation / Input | blank task title accepted |
| UI / Cosmetic | error not shown in red |
| Security | `/tasks` opens without login |
| Session / State | still logged in after logout |
| Crash / Exception | HTTP 500 on an invalid task index |
| Automation / Test | stale element in a Selenium script |

Severity: Critical (crash or data loss), Major (main feature broken), Minor (small defect), Trivial (cosmetic).

## How the Code / Document Works

Folder `9_MiniProject_TestIntegration/` contains `app.py`, `report.py`, `test_unit_integration.py`, `test_selenium_regression.py`, `TaskTrack.side`, `test_plan.md`, and the generated `test_report_unit.txt` and `test_report_selenium.txt`.

### The application (`app.py`)
A small Flask web app. Storage is in memory (`users` and `tasks` dictionaries), so data resets on restart.

**Validation functions** (white-box targets):

```python
def validate_password(password):
    if len(password) < 6:
        return "Password must be at least 6 characters"
    if not re.search(r"\d", password):
        return "Password must contain a digit"
    return ""
```
They return `""` when valid, otherwise an error message. Rules: username `[A-Za-z0-9_]{3,15}`; password at least 6 characters with a digit; task title 1 to 50 characters after `strip()`.

**Routes**

| Route | Behaviour |
| --- | --- |
| `/` | redirect to tasks if logged in, else to login |
| `/register` (GET, POST) | validate, check passwords match, check username unique ignoring case, then show Login with "Registration successful, please login" |
| `/login` (GET, POST) | blank gives "Enter username and password", mismatch gives "Invalid username or password", success stores `session["user"]` |
| `/logout` | removes the user from the session |
| `/tasks` | list page, redirects to login if not logged in |
| `/tasks/add` (POST) | validate title, append task |
| `/tasks/<int:i>/<action>` | `done` or `delete`; an out-of-range index is ignored (no crash) |

**Test-friendly HTML**: the template gives elements fixed ids (`username`, `password`, `confirm`, `submit`, `heading`, `error`, `msg`, `task-title`, `add-task`, `task-list`, `count`, `logout`) which the Selenium scripts use as locators.

**The helper that caused DEF-001:**

```python
def page(**kw):
    return render_template_string(PAGE, **{"error": "", "msg": "", **kw})
```

### Report generator (`report.py`)
`run_and_report(test_classes, title, report_file)` runs a unittest suite and writes a text report with one line per test (name, PASS/FAIL/ERROR and description), totals, a verdict, and a "DEFECT" line for each failure.

```python
if rate == 100:        verdict = "ACCEPTED"
elif rate >= 90:       verdict = "ACCEPTED WITH MINOR DEFECTS"
else:                  verdict = "REJECTED"
```

Both test files use it.

### Unit and integration tests (`test_unit_integration.py`): 19 tests
| Class | Tests | Kind |
| --- | --- | --- |
| `WhiteBoxValidation` | 9 | each branch of the three validators |
| `BlackBoxRegister` | 5 | BVA on username length 3, 15, 16; password mismatch; duplicate user in a different case |
| `BlackBoxLogin` | 3 | empty fields, wrong password, `/tasks` redirects when logged out |
| `IntegrationFlow` | 2 | full journey; invalid task index does not crash |

Black-box tests use the **Flask test client** (`app.test_client()`) so no real server or browser is needed. `setUp` clears `users` and `tasks` for independence.

```python
def test_username_boundary_over(self):
    """BVA: username length 16 is rejected"""
    self.assertIn(b"3-15", self.register("a" * 16).data)
```

### Selenium regression suite (`test_selenium_regression.py`): 10 tests
- `setUpClass` starts the Flask app **inside the test** on port 5001 using `werkzeug.serving.make_server` in a thread, and opens a browser. So `app.py` need not be run separately.
- Environment variables: `BROWSER=edge` and `HEADLESS=1`. `implicitly_wait(3)` is set.
- `setUp` clears users, tasks and cookies before every test.
- Tests RT-01 to RT-10: login page loads, valid registration, weak password, invalid login, valid login, add task, blank task, complete task, delete task, logout.

**Important helper, `click_and_wait`:** `click()` returns before the next page has loaded, so a script may read the OLD page. The helper keeps the old `<html>` element and waits until it becomes stale (the page changed).

```python
old_page = self.find("html")
self.find(css).click()
...
WebDriverWait(self.driver, 10).until(old_page_gone)
```

This is the fix for BUG-02 (a stale element or timing error found by the Selenium run) and shows why waits matter.

### Selenium IDE (`TaskTrack.side`)
A JSON project with two tests and one suite named **Regression**:

1. "Register login add task logout" (16 commands: `open`, `type`, `click`, `assertText` with targets such as `id=username`, `css=#task-list .title`).
2. "Invalid login shows error" (5 commands).

```json
{ "command": "assertText", "target": "id=error", "value": "Invalid username or password" }
```

The IDE project uses user `ideuser`, and the app must be running at `http://127.0.0.1:5000`.

### The test plan (`test_plan.md`)
Sections: 1 Environment, 2 Test plan (objective; features F1 to F6: registration, login, add, complete, delete task, logout/session; features not tested; approach table; entry and exit criteria; acceptance criteria; deliverables), 3 Bug taxonomy, 4 Test cases TC01 to TC17 with procedures, 5 Regression scripts, 6 Bugs identified, 7 Exploratory testing, 8 Test report summary.

**Bugs identified**

| ID | Found by | Description | Severity | Status |
| --- | --- | --- | --- | --- |
| BUG-01 | unit/integration tests | every error message crashed the server (HTTP 500, `TypeError`) | Critical | Fixed in `page()` |
| BUG-02 | Selenium regression | stale element when logging in straight after registering | Major | Fixed (open `/login` before typing) |
| BUG-03 | exploratory | Done and Delete are GET links, so a prefetch could change data | Minor | Open, accepted for the lab version |

**Exploratory session (charter: Register and Task pages for 20 minutes).** Seven observations, all Pass, for example: username with spaces rejected; same username in a different case rejected; task of 50 characters accepted and 51 rejected; `<b>hi</b>` shown as plain text (Jinja escapes it); Back button after logout shows the cached page but every action redirects to login; `/tasks/-1/delete` gives 404.

**Summary:** Unit and Integration 19/19, Selenium 10/10, Exploratory 7/7. Only BUG-03 (Minor) is open, so the verdict is **ACCEPTED**.

## How to Run and Expected Output

```bash
pip install -r ../requirements.txt     # selenium, openpyxl, flask, coverage
cd 9_MiniProject_TestIntegration
python app.py                          # use the app at http://127.0.0.1:5000
python test_unit_integration.py        # writes test_report_unit.txt
python test_selenium_regression.py     # writes test_report_selenium.txt
```

Set `HEADLESS=1` to hide the browser window, or `BROWSER=edge` to use Edge. Chrome or Edge must be installed (Selenium Manager downloads the driver).

Expected results:

```
Total: 19   Passed: 19   Failed: 0   Pass rate: 100.0%
Verdict: ACCEPTED
```
for the unit and integration run, and

```
Total: 10   Passed: 10   Failed: 0   Pass rate: 100.0%
Verdict: ACCEPTED
```
for the Selenium run. The console also prints `Report written to <file>  ->  ACCEPTED`.

**Selenium IDE:** install the extension in Chrome or Edge, choose **Open an existing project**, select `TaskTrack.side`, start `python app.py`, then run the **Regression** suite. Users are stored in memory, so **restart `app.py` before running again**, otherwise `ideuser` already exists.

With Docker (from the `STQA` folder): `docker compose up --build -d tasktrack` serves the app at `http://localhost:5000`.

## Related Concepts and Real-World Tools

- **Frameworks**: pytest, JUnit/TestNG with Selenium. Page Object Model for maintainable scripts.
- **Modern UI automation**: Cypress, Playwright (auto-waiting reduces flaky tests).
- **Visual and cross-browser**: BrowserStack, Sauce Labs, Percy.
- **Selenium Grid** runs the regression suite on many browsers in parallel (Assignment 5).
- **CI**: Jenkins, GitHub Actions run the regression suite on every commit, so regressions are found at once.
- **Bug tracking**: JIRA, Bugzilla (Assignment 4).
- **Exploratory tools**: session-based test management, screen recorders, browser DevTools.
- **Web security**: using POST plus CSRF tokens for state changes (BUG-03), OWASP ZAP.

## Viva Questions

1. **What is regression testing and why automate it?**
   Re-running earlier tests after a change to confirm nothing broke. It is repeated often, so automation saves time and is more reliable.

2. **What is exploratory testing and how is it different from scripted testing?**
   The tester learns, designs and executes tests at the same time within a time-boxed charter. Scripted testing follows pre-written cases.

3. **What is Selenium IDE?**
   A browser extension that records user actions as a test and plays them back. The project is saved in a `.side` file.

4. **Difference between Selenium IDE and WebDriver?**
   IDE is record and playback with little coding. WebDriver is a programming API (Python here), which is more flexible, supports loops, conditions and frameworks.

5. **What is a stale element exception and how did you handle it?**
   It occurs when a stored element no longer exists because the page reloaded. My `click_and_wait` helper waits until the old page goes stale before reading the new page.

6. **What is the bug taxonomy of your project?**
   Functional, validation, UI, security, session/state, crash and automation/test defects, each with a severity of Critical, Major, Minor or Trivial.

7. **Which bug did the unit tests find and why was it Critical?**
   Every validation error crashed the server (HTTP 500) because `page()` passed the keyword `error` twice. It broke all forms, so it was Critical. It was fixed by merging defaults with the caller's values.

8. **What is the open bug BUG-03?**
   Done and Delete use GET links, so visiting a URL changes data. It is Minor and accepted for the lab version. The fix is POST forms with CSRF tokens.

9. **How do the black-box tests run without a browser?**
   They use Flask's test client to send HTTP requests directly to the app and check the response.

10. **How is the acceptance decision made?**
    By pass rate: 100% is ACCEPTED, at least 90% with only minor bugs open is ACCEPTED WITH MINOR DEFECTS, below 90% is REJECTED. All suites passed and only a Minor bug is open, so the application is accepted.
