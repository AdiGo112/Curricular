# Assignment 3: Test Cases in an Excel Sheet (Social Media Application)

## Aim
Write test cases in an Excel sheet for a social media application or website.

## Theory and Fundamentals

### What is a test case?
A test case is a documented set of conditions, steps and data used to check one specific behaviour, with an expected result. It is the detailed form of a test scenario.

### Fields of a good test case
| Field | Purpose |
| --- | --- |
| Test Case ID | Unique reference (TC01, TC02 ...) |
| Module | Part of the application (Login, Post ...) |
| Test Scenario | What is being checked |
| Pre-condition | State needed before the test starts (for example "user is logged in") |
| Test Steps | Numbered actions the tester performs |
| Test Data | Exact values to enter |
| Expected Result | What the application should do |
| Actual Result | What really happened (filled during execution) |
| Status | Pass, Fail, Blocked or Not Run |
| Priority | How important the test is (High, Medium, Low) |
| Remarks | Notes, defect ID |

### Status values
- **Pass**: actual equals expected.
- **Fail**: actual differs from expected, so log a defect.
- **Blocked**: cannot be run because something else is broken (for example login fails, so posting cannot be tested).
- **Not Run**: not yet executed.

### Test design techniques seen in the sheet
- **Positive and negative cases**: valid registration versus used email, weak password, blank field.
- **Equivalence partitioning**: valid file (`photo.jpg`) and invalid file (`virus.exe`) are two classes.
- **Boundary value analysis**: bio of 200 characters against a limit of 150.
- **Security testing**: script in a comment (XSS), Back button after logout.
- **Pre-conditions** make each test independent and repeatable.

### Why Excel?
Excel is the most common low-cost test management tool. It supports filters, drop-downs, colours and formulas, so a team can track execution without special software.

## How the Code / Document Works

`3_SocialMediaTestCases.py` uses the `openpyxl` library to **generate** `SocialMedia_TestCases.xlsx`. This keeps the test cases in one reviewable place and rebuilds the sheet at any time.

### The data
`TEST_CASES` is a list of tuples `(Module, Scenario, Pre-condition, Steps, Test Data, Expected, Priority)`. There are 30 test cases:

| Module | Count | Examples |
| --- | --- | --- |
| Sign Up | 4 | valid, used email, weak password, blank name |
| Login | 4 | valid, wrong password, blank, forgot password |
| Profile | 4 | picture upload, `.exe` upload, bio too long, private account |
| Post | 4 | create, empty post, edit, delete |
| Interaction | 5 | like, unlike, comment, empty comment, share |
| Follow | 2 | public and private account |
| Search | 2 | existing user, special characters |
| Messaging, Notifications, Logout | 1 each | |
| Security | 2 | session after logout, XSS in comment |

A real row from the file:

```python
("Security", "Script in comment (XSS)", "Post visible",
 "1. Add comment with script", "<script>alert(1)</script>",
 "Shown as text, script not executed", "High"),
```

### `build_workbook(path)`
1. **Sheet "Test Cases"**: a merged title row, then a blue header row (11 columns, white bold text, set column widths), then one row per test case. IDs are generated as `TC01`, `TC02` and so on with `f"TC{i:02d}"`. Actual Result is empty, Status starts as "Not Run".
2. **Drop-down** on the Status column using `DataValidation`:

```python
dv = DataValidation(type="list", formula1='"Pass,Fail,Blocked,Not Run"', allow_blank=True)
dv.add(f"I{header_row + 1}:I{last_row}")
```

3. **Usability features**: `freeze_panes` keeps header and the first two columns visible when scrolling, and `auto_filter` lets you filter by Module, Priority or Status.
4. **Sheet "Summary"**: counts are **Excel formulas**, so they update when you change a status.

```python
summary.append([status, f'=COUNTIF({status_range},"{status}")'])
summary.append(["Total", f"=COUNTA({status_range})"])
summary.append(["Pass %", '=IF(B8=0,0,B4/B8)'])
```

The Pass % formula uses fixed cells (B4 is the Pass count and B8 is the Total), which match the row layout that the code creates.

## How to Run and Expected Output

```bash
pip install openpyxl
python 3_SocialMediaTestCases.py
```

Output printed to the console:

```
Created SocialMedia_TestCases.xlsx with 30 test cases.
```

Then:
1. Open `SocialMedia_TestCases.xlsx` in Excel (or LibreOffice).
2. Execute each test on a social media app, type the observed result in **Actual Result**, and pick Pass, Fail or Blocked from the drop-down.
3. Open the **Summary** sheet to see the counts and pass percentage.

Note: the formulas calculate when the file is opened in Excel. A viewer that does not calculate formulas may show them empty.

## Related Concepts and Real-World Tools

- **Test management tools**: TestRail, Zephyr, Xray, qTest and Azure Test Plans replace Excel in larger teams. They add history, requirement links and dashboards.
- **Requirements Traceability Matrix (RTM)**: a table mapping each requirement to its test cases.
- **Test case review**: peers review test cases for coverage before execution.
- **Defect tracking**: a Fail row should be linked to a defect in JIRA or Bugzilla (see Assignment 4).
- **Data-driven automation**: test data from Excel or CSV can feed Selenium or pytest tests.
- **Libraries**: `openpyxl` (used here), `pandas` and `xlsxwriter` generate Excel files from Python. Apache POI does the same in Java.

## Viva Questions

1. **What is a test case? List its main fields.**
   A set of steps, data and an expected result to verify one behaviour. Main fields: ID, scenario, pre-condition, steps, test data, expected result, actual result, status, priority.

2. **What is the difference between "Fail" and "Blocked"?**
   Fail means the test ran and the actual result differs from expected. Blocked means the test could not run because of another problem, for example a broken login.

3. **Why is a pre-condition written in each test case?**
   It states the starting state, so anyone can repeat the test and get the same result.

4. **Which test design techniques did you use?**
   Equivalence partitioning (valid and invalid file types), boundary value analysis (bio length), positive and negative testing, and security checks (XSS, session).

5. **How does the Summary sheet update automatically?**
   It uses formulas such as `COUNTIF` over the Status column, so changing a status recalculates the counts.

6. **Why did you add a drop-down to the Status column?**
   It limits entries to Pass, Fail, Blocked or Not Run, which avoids spelling mistakes and keeps the counts correct.

7. **Why generate the Excel file using Python?**
   The test cases stay in one script that can be reviewed and rebuilt, and formatting, formulas and drop-downs are consistent.

8. **What does priority mean in a test case?**
   It shows how important a test is, so High tests (login, posting) are run first when time is short.

9. **Give one negative and one security test case from your sheet.**
   Negative: register with an already used email. Security: post a comment containing `<script>alert(1)</script>`, which must be shown as text.

10. **Why would a large project not use only Excel?**
    Excel has no version history, requirement linking or multi-user execution tracking. Tools like TestRail or Xray provide these.
