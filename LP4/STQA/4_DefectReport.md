# Assignment 4: Defect Report

## What is a Defect Report?
A defect (bug) report records a difference between the **expected** and the **actual** behaviour of an application. It gives developers enough information to reproduce, fix and verify the problem.

**Application under test:** TaskTrack web application (the Mini Project in `9_MiniProject_TestIntegration/`). Both defects below were really found while testing it.

---

## Defect Report 1

| Field | Details |
| --- | --- |
| **Defect ID** | DEF-001 |
| **Project / Application** | TaskTrack v1.0 (Flask web app) |
| **Module** | Registration / Login / Add Task (all forms) |
| **Title / Summary** | Server crashes (HTTP 500) whenever a validation error message must be shown |
| **Reported By** | Tester |
| **Reported On** | 03-11-2026 |
| **Assigned To** | Developer |
| **Environment** | Windows 11, Python 3.13, Flask 3, Chrome |
| **Build / Version** | 1.0 |
| **Found In** | Unit / Integration testing (during development) |
| **Severity** | Critical |
| **Priority** | P1 (High) |
| **Status** | Closed |

**Pre-condition:** the application is running at `http://127.0.0.1:5000`.

**Steps to Reproduce:**
1. Open `http://127.0.0.1:5000/login`
2. Leave Username and Password blank
3. Click **Login**

**Test Data:** Username = (blank), Password = (blank)

**Expected Result:** the Login page shows the error "Enter username and password".

**Actual Result:** "500 Internal Server Error" page. The console shows:
```
TypeError: render_template_string() got multiple values for keyword argument 'error'
```

**Root Cause:** the helper `page()` always passed `error=""` and also received `error=...` from the caller, so Python got the same argument twice.

**Fix:** merge the default values with the caller's values before rendering:
```python
return render_template_string(PAGE, **{"error": "", "msg": "", **kw})
```

**Verification:** all previously failing test cases now pass. Defect closed.

**Attachments:** console stack trace

---

## Defect Report 2

| Field | Details |
| --- | --- |
| **Defect ID** | DEF-002 |
| **Project / Application** | TaskTrack v1.0 |
| **Module** | Tasks (Done / Delete) |
| **Title / Summary** | Task state changes through GET links, so they can be triggered without user action |
| **Reported By** | Tester |
| **Reported On** | 03-11-2026 |
| **Environment** | Windows 11, Chrome |
| **Found In** | Exploratory testing |
| **Severity** | Minor |
| **Priority** | P3 (Low) |
| **Status** | Deferred (accepted for lab version) |

**Steps to Reproduce:**
1. Log in and add a task
2. In the same browser, open `http://127.0.0.1:5000/tasks/0/delete` directly (or from a link on another page)

**Expected Result:** data should change only when the user submits a form (POST request).

**Actual Result:** the task is deleted just by visiting the URL.

**Suggested Fix:** change Done/Delete to small POST forms with a CSRF token.

---

## Defect Life Cycle

```
 New ──> Assigned ──> Open ──> Fixed ──> Retest ──> Verified ──> Closed
  │                    │                   │
  │                    ├──> Rejected       └──> Reopened ──> Assigned
  │                    ├──> Duplicate
  └────────────────────└──> Deferred
```

| State | Meaning |
| --- | --- |
| New | Tester has logged the defect |
| Assigned | Lead has given it to a developer |
| Open | Developer is analysing / fixing |
| Fixed | Code changed, ready for retest |
| Retest | Tester re-runs the failing test |
| Verified / Closed | Fix confirmed |
| Reopened | Defect still occurs after the fix |
| Rejected / Duplicate / Deferred | Not a defect / already reported / fix postponed |

## Severity vs Priority

| | **High Priority** | **Low Priority** |
| --- | --- | --- |
| **High Severity** | App crashes on login (DEF-001) | Crash in a rarely used admin report |
| **Low Severity** | Company logo misspelled on home page | Small spacing issue on the Help page |

- **Severity:** how much the defect affects the system (set by the tester).
- **Priority:** how soon it must be fixed (set by the lead or manager).
