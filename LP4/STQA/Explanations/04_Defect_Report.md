# Assignment 4: Defect Report

## Aim
Create a defect report for any application or web application.

## Theory and Fundamentals

### Defect, bug, error, failure
| Term | Meaning |
| --- | --- |
| **Error (mistake)** | A human mistake by the developer. |
| **Defect / Bug / Fault** | A flaw in the code or document caused by the mistake. |
| **Failure** | The wrong behaviour seen when the defective code runs. |

A defect report records a difference between **expected** and **actual** behaviour. It must give the developer enough detail to reproduce, fix and verify the problem.

### Fields of a good defect report
Defect ID, title, module, build/version, environment, severity, priority, status, reported by and date, assigned to, steps to reproduce, test data, expected result, actual result, attachments (screenshots, logs). A report must be **specific, reproducible, neutral in tone and written once per defect**.

### Severity vs priority
- **Severity**: how badly the defect affects the system. Usually set by the tester.
- **Priority**: how soon it must be fixed. Usually set by the lead or manager.

| | High priority | Low priority |
| --- | --- | --- |
| **High severity** | App crashes on login | Crash in a rarely used admin report |
| **Low severity** | Company name misspelled on the home page | Small spacing issue on the Help page |

### Severity levels
Critical (crash, data loss), Major (main feature broken), Minor (small defect, workaround exists), Trivial (cosmetic).

### Defect life cycle
```
New -> Assigned -> Open -> Fixed -> Retest -> Verified -> Closed
Other paths: Rejected, Duplicate, Deferred, Reopened (if the fix fails)
```

| State | Meaning |
| --- | --- |
| New | Tester logged the defect |
| Assigned | Lead gave it to a developer |
| Open | Developer is working on it |
| Fixed | Code changed, ready for retest |
| Retest | Tester runs the failing test again |
| Verified / Closed | Fix confirmed |
| Reopened | Still fails after the fix |
| Rejected / Duplicate / Deferred | Not a defect / already reported / fix postponed |

### Root cause and verification
A good report also records the **root cause** (why it happened) and **verification** (which tests prove the fix). This helps prevent the same type of bug.

## How the Code / Document Works

`4_DefectReport.md` is a document. The application under test is **TaskTrack** (the Flask web app of Mini Project 9). Both defects were found while testing it.

### Defect 1: DEF-001 (Critical, P1, Closed)
- **Title:** server crashes (HTTP 500) whenever a validation error message must be shown.
- **Found in:** unit/integration testing (`test_unit_integration.py`).
- **Steps:** open `/login`, leave both fields blank, click Login.
- **Expected:** the message "Enter username and password".
- **Actual:** "500 Internal Server Error". The console shows `TypeError: render_template_string() got multiple values for keyword argument 'error'`.
- **Root cause:** the helper `page()` passed `error=""` itself and also received `error=...` from the caller, so the argument was given twice.
- **Fix:** merge defaults with the caller's values.

```python
return render_template_string(PAGE, **{"error": "", "msg": "", **kw})
```

- **Verification:** the 9 failing test cases now pass (19/19), so the defect is closed.

This matches the real `page()` function in `9_MiniProject_TestIntegration/app.py`.

### Defect 2: DEF-002 (Minor, P3, Deferred)
- **Title:** task state changes through GET links.
- **Found in:** exploratory testing.
- **Steps:** log in, add a task, then open `http://127.0.0.1:5000/tasks/0/delete` directly.
- **Actual:** the task is deleted just by visiting the URL.
- **Suggested fix:** use POST forms with a CSRF token.
- **Status:** Deferred (accepted for the lab version).

### Why the two defects are classified differently
| | DEF-001 | DEF-002 |
| --- | --- | --- |
| Effect | Whole page crashes for every error | Data can be changed by a link |
| Severity | Critical | Minor |
| Priority | P1 (fix at once) | P3 (can wait) |
| End state | Closed (fixed) | Deferred |

The document then explains the defect life cycle (diagram and state table) and the severity versus priority matrix, using DEF-001 as the High-High example.

## How to Run and Expected Output

Nothing to run. To see the defect for yourself (optional), use the TaskTrack project:

```bash
cd 9_MiniProject_TestIntegration
python test_unit_integration.py
```

The report `test_report_unit.txt` shows 19 tests, all passing now. The DEF-001 test cases passed only after the fix in `page()` was applied.

For DEF-002: run `python app.py`, log in, add a task and open `http://127.0.0.1:5000/tasks/0/delete` in the same browser. The task disappears.

## Related Concepts and Real-World Tools

- **Defect tracking tools**: JIRA, Bugzilla, Mantis, Azure DevOps and GitHub Issues. They keep the life cycle, assignees, comments and attachments.
- **Screenshots and screen recorders**: Snagit, Loom and browser DevTools (console and network tabs) provide evidence.
- **Log analysis**: stack traces such as the `TypeError` above are copied into the report.
- **Defect metrics**: defect density, defect leakage (bugs found by users after release), defect removal efficiency.
- **Defect triage**: a meeting where severity, priority and owner are decided.
- **CSRF and HTTP method safety (DEF-002)**: GET requests should be "safe" and not change data. Frameworks such as Flask-WTF add CSRF tokens.

## Viva Questions

1. **What is a defect report and why is it needed?**
   It is a record of the difference between expected and actual behaviour. It lets developers reproduce, fix and verify the problem.

2. **Explain error, defect and failure.**
   An error is a human mistake. It causes a defect in the code. When the code runs the defect may cause a failure, which the user sees.

3. **What is the difference between severity and priority?**
   Severity is the technical impact of the bug (set by the tester). Priority is the urgency of fixing it (set by the lead or manager).

4. **Give an example of high severity with low priority.**
   A crash in a rarely used admin report. The impact is big, but few users are affected, so it can wait.

5. **Explain the defect life cycle.**
   New, Assigned, Open, Fixed, Retest, then Verified/Closed. If the retest fails it is Reopened. Defects can also be Rejected, Duplicate or Deferred.

6. **What is the root cause of DEF-001?**
   The `page()` helper passed `error=""` and the caller also passed `error`, so Python received the same keyword twice and raised a `TypeError`.

7. **What makes a defect report good?**
   Clear title, exact reproducible steps, test data, expected and actual result, environment, severity, and evidence. It must also be neutral and cover only one defect.

8. **Why was DEF-002 marked Deferred?**
   It is minor (low severity, P3) and the app is only a lab version, so the fix, using POST forms and CSRF tokens, was postponed.

9. **What does "Reopened" mean?**
   The tester retested the fix and the bug still occurs, so it goes back to the developer.

10. **How was DEF-001 verified as fixed?**
    The previously failing test cases were run again. All 19 unit and integration tests passed, so the defect was closed.
