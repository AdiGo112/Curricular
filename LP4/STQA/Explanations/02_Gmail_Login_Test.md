# Assignment 2: Gmail Login Test (Scenarios Executed)

## Aim
Test scenarios for the Gmail login page: execute the scenarios written in Assignment 1.

## Theory and Fundamentals

### Test automation
Running the same checks by hand again and again is slow and error-prone. A script that runs scenarios and compares **expected** and **actual** results is a simple form of test automation.

### Anatomy of an automated test
Every automated check has four parts:

1. **Input** (test data)
2. **Action** (call the system under test)
3. **Expected result** (what should happen)
4. **Verdict** (PASS if actual equals expected, otherwise FAIL)

### System under test (SUT) and a simulator (stub)
Google blocks automated logins on the real page with CAPTCHA and "This browser may not be secure". So the code contains a small **simulator** that follows the same rules as the Gmail login page. A simulator is a fake, simple version of a real system used when the real one cannot be tested repeatedly. Its results are repeatable, and there is no risk of locking a real account.

### Data-driven testing
All scenarios are stored in a list (data) and one function runs them all. To add a test you add one row, not a new function.

### Positive, negative and boundary ideas used
- Positive: registered email, correct password.
- Negative: blank, unregistered, invalid format, wrong password.
- Security: SQL injection and script text must be rejected as invalid input.
- Boundary: lockout after exactly `MAX_ATTEMPTS = 3` wrong passwords.
- Normalisation: spaces are trimmed and case is ignored for emails (TS07, TS08).

### Regular expression
The email format is checked with a regex. A regex is a pattern describing allowed text. `re.fullmatch` means the **whole** text must match, not just a part.

## How the Code / Document Works

`2_GmailLoginTest.py` has three parts: the simulator, the scenario table and the runner.

### 1. The simulator
Two fake accounts are stored in a dictionary. One has 2-step verification on.

```python
ACCOUNTS = {
    "student.stqa@gmail.com": {"password": "Test@1234", "phone": "9876543210", "two_step": False},
    "secure.user@gmail.com": {"password": "Secure#99", "phone": "9123456780", "two_step": True},
}
MAX_ATTEMPTS = 3   # after this many wrong passwords, CAPTCHA is required
```

**Screen 1: `GmailLogin.enter_email(text)`** goes through these checks in order:

| Step | Check | Returns |
| --- | --- | --- |
| 1 | `strip()` spaces | (continues) |
| 2 | blank | "Enter an email or phone number" |
| 3 | all digits, so a phone number | `PASSWORD_SCREEN` if a phone matches, else "Couldn't find your Google Account" |
| 4 | lower-case it, add `@gmail.com` if there is no `@` | (continues) |
| 5 | regex format check | "Enter a valid email or phone number" |
| 6 | email not in `ACCOUNTS` | "Couldn't find your Google Account" |
| 7 | otherwise | `PASSWORD_SCREEN` |

The format check is:

```python
if not re.fullmatch(r"[a-z0-9._]+@[a-z0-9-]+\.[a-z]{2,}", email):
    return "Enter a valid email or phone number"
```

Because `<`, `'` and spaces are not allowed by this regex, the SQL injection text `' OR '1'='1` and `<script>alert(1)</script>` are rejected as invalid (TS28, TS29).

**Screen 2: `GmailLogin.enter_password(password)`**

```python
if password == "":
    return "Enter a password"
if self.wrong_attempts >= MAX_ATTEMPTS:
    return "CAPTCHA_REQUIRED"
...
if password != acc["password"]:
    self.wrong_attempts += 1
    return "Wrong password. Try again or click Forgot password to reset it."
self.wrong_attempts = 0
return "OTP_SCREEN" if acc["two_step"] else "INBOX"
```

Passwords are compared exactly, so case matters (TS14). Once the counter reaches 3, even the correct password returns `CAPTCHA_REQUIRED` (TS17).

### 2. The scenario table
Each row is `(ID, description, email, password, expected)`. `password = None` means only the email screen is tested.

```python
("TS04", "Blank email", "", None, "Enter an email or phone number"),
("TS11", "Correct password", "student.stqa@gmail.com", "Test@1234", "INBOX"),
("TS18", "2-Step Verification account", "secure.user@gmail.com", "Secure#99", "OTP_SCREEN"),
```

The table has 15 rows: TS01 to TS08, TS11 to TS14, TS18, TS28, TS29.

### 3. The runner
- `run_scenario(email, password)` creates a **fresh** `GmailLogin` for each scenario, so tests do not affect each other, and returns the final result.
- `run_lockout_scenario()` is TS17. It enters the email, tries a wrong password 3 times, then the correct one, and expects `CAPTCHA_REQUIRED`.
- The `__main__` block runs all 15 plus TS17 (16 in total), prints a table and a summary, then exits with code 0 (all pass) or 1 (any failure). The exit code is what a CI server checks.

```python
status = "PASS" if actual == expected else "FAIL"
```

Scenarios not coded (UI, compatibility, performance, TS09, TS10, TS15, TS16, TS19 and others) are not suitable for this simulator and are done manually in Assignment 1.

## How to Run and Expected Output

```bash
python 2_GmailLoginTest.py
```

No extra library is needed (only `re` from the standard library).

Expected output: a header, one line per scenario with ID, name, expected, actual (both cut to 15 characters) and PASS or FAIL, then a summary. It ends with:

```
Total: 16   Passed: 16   Failed: 0
All scenarios passed.
```

(The count of 16 comes from 15 table rows plus TS17.) If any row fails, "Some scenarios FAILED - check above." is printed and the exit code is 1.

## Related Concepts and Real-World Tools

- **pytest / unittest / JUnit / TestNG**: real test frameworks. `pytest.mark.parametrize` and TestNG `@DataProvider` do the same job as the `SCENARIOS` list.
- **Mocking / stubbing**: `unittest.mock`, Mockito and WireMock replace real services with fakes, as the simulator does here.
- **UI automation of the real page**: Selenium, Playwright or Cypress. Google blocks bots, so teams use test accounts or the Google test environment.
- **Continuous Integration**: Jenkins, GitHub Actions and GitLab CI run scripts like this on every commit and fail the build if the exit code is not 0.
- **Lockout / CAPTCHA**: in production this is handled by identity providers (Google reCAPTCHA, Auth0). Tests usually mock them.

## Viva Questions

1. **Why did you use a simulator instead of the real Gmail page?**
   Google blocks automated logins with CAPTCHA and security warnings. A local copy of the same rules gives repeatable results.

2. **How does the script decide PASS or FAIL?**
   It compares the actual result returned by the simulator with the expected result in the table. Equal means PASS.

3. **What is data-driven testing?**
   Test data and expected results are kept in a table and one common function runs them all. Adding a test means adding a row.

4. **Why is a new `GmailLogin` object created for each scenario?**
   So that earlier tests, such as wrong-password counts, cannot affect the next test. Tests must be independent.

5. **How does the code stop SQL injection and script text?**
   The email regex allows only letters, digits, dot, underscore, `@` and `-`. Quotes, spaces and angle brackets fail the check, so they are reported as invalid.

6. **What does TS17 test and how?**
   Account lockout. It enters 3 wrong passwords and then the correct one. The expected result is `CAPTCHA_REQUIRED`.

7. **What is `re.fullmatch` and why not `re.search`?**
   `fullmatch` needs the entire string to match the pattern. `search` would accept a valid email hidden inside other text, which is wrong for validation.

8. **Why does the script call `raise SystemExit(0 or 1)`?**
   The exit code tells tools such as `run_all.py` or a CI server whether the run passed.

9. **Which scenarios from Assignment 1 are not automated here and why?**
   UI, compatibility and performance ones, and a few functional ones (such as the link checks TS09, TS10). They need a real browser or devices, so they are tested manually.

10. **Is this black-box or white-box testing?**
    It is black-box: scenarios use only inputs and expected outputs. The simulator code is only the system under test and the tests do not depend on its internals.
