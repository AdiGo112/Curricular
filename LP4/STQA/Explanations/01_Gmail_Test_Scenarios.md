# Assignment 1: Test Scenarios for the Gmail Login Page

## Aim
Write test scenarios for the Gmail login page.

## Theory and Fundamentals

### Test scenario vs test case
| Term | Meaning | Example |
| --- | --- | --- |
| **Test scenario** | A one-line statement of *what* to test. No detailed steps. | "Login with a wrong password" |
| **Test case** | A detailed set of steps, test data, expected result and pass/fail status for one condition. | Step 1: open page. Step 2: type `wrong123`. Step 3: click Next. Expected: error message. |

One scenario usually gives several test cases. Scenarios are written first because they are quick to write and easy for a manager or client to review. They also show how much of the feature you have covered.

### Why scenarios are grouped by type
A good scenario list does not only check "does login work?". It covers different quality aspects:

- **Functional**: does each feature do what the requirement says?
- **UI / Usability**: is the screen clear, aligned and easy to use?
- **Security**: can an attacker break in or steal data?
- **Compatibility**: does it work on different browsers, devices and operating systems?
- **Performance**: is it fast enough?

### Positive and negative testing
- **Positive testing**: give valid input and check that the system works (correct password opens the inbox).
- **Negative testing**: give invalid input and check that the system rejects it politely (blank password shows "Enter a password"). The system must not crash.

### Black-box thinking
The tester does not see Gmail's source code. Scenarios are derived only from the visible behaviour of the page and from common sense. This is **black-box testing**.

### Equivalence partitioning in the scenarios
Inputs are divided into groups where the system should behave the same way. Only one value per group needs testing.

| Email field group | Representative value |
| --- | --- |
| Valid registered email | a registered Gmail address |
| Valid format but not registered | an unregistered email |
| Invalid format | `abc@@gmail` |
| Blank | (nothing) |

## How the Code / Document Works

`1_GmailTestScenarios.md` is a document only, with no code. It has this structure.

**Application under test:** `https://accounts.google.com`. Gmail logs in over two screens: first email or phone then **Next**, then password then **Next**.

**36 scenarios (TS01 to TS36)** in five tables. Each row has ID, Test Scenario and Expected Result.

| Section | IDs | What it covers |
| --- | --- | --- |
| A. Functional: Email screen | TS01 to TS10 | valid email, username only, phone, blank, unregistered, invalid format, spaces, upper case, "Forgot email?", "Create account" |
| B. Functional: Password screen | TS11 to TS19 | correct, wrong, blank, wrong case, show password, forgot password, many wrong attempts, 2-step verification, Enter key |
| C. UI / Usability | TS20 to TS25 | logo and fields visible, labels, Tab order, language drop-down, responsive layout, footer links |
| D. Security | TS26 to TS32 | masked password, HTTPS, SQL injection, script injection, Back button after logout, copy blocked, new-device alert |
| E. Compatibility and Performance | TS33 to TS36 | browsers, operating systems, load time, slow network |

Sample rows from the real document:

```
| TS05 | Enter an unregistered email | Error "Couldn't find your Google Account" |
| TS12 | Enter a wrong password      | Error "Wrong password. Try again…" |
| TS28 | Try SQL injection (' OR '1'='1) in the email field | Treated as an invalid email |
```

The document ends with a split into positive and negative scenarios:

- **Positive:** TS01, TS02, TS03, TS07, TS08, TS11
- **Negative:** TS04, TS05, TS06, TS12, TS13, TS14, TS28, TS29

The last line says Assignment 2 (`2_GmailLoginTest.py`) automatically runs the functional and security scenarios.

### What makes these scenarios good
- Each one is a single idea with a single observable result.
- The expected results quote real message texts, so a tester can compare directly.
- The boundary conditions of the email screen (blank, invalid, unregistered, with spaces, upper case) are all present.

## How to Run and Expected Output

Nothing to run. Open the file in any Markdown viewer or editor.

To use it in a lab or exam:
1. Open `https://accounts.google.com` in a browser.
2. Go through each scenario, perform it and compare the real result with the Expected Result column.
3. Note Pass or Fail. Some scenarios (TS17 lockout, TS32 security alert, TS33 to TS36) need extra devices, many attempts or a real account, so they are normally done manually.

## Related Concepts and Real-World Tools

- **Test case management tools**: TestRail, Zephyr, qTest and Xray (inside JIRA) store scenarios and cases, link them to requirements and report coverage.
- **Gherkin / BDD**: scenarios can be written as "Given / When / Then" and executed by Cucumber or `behave`.
- **Security testing**: OWASP ZAP and Burp Suite test SQL injection and XSS (TS28, TS29) automatically.
- **Cross-browser tools**: BrowserStack and Sauce Labs cover TS33 and TS34 on many real browsers and devices.
- **Performance tools**: Lighthouse, JMeter and k6 measure load time (TS35).
- **Authentication in real projects**: 2-Step Verification and CAPTCHA (TS17, TS18) are often tested with test accounts or mocks because they block automation.

## Viva Questions

1. **What is a test scenario?**
   A one-line description of a feature or situation to be tested, without detailed steps. Example: "Enter an unregistered email".

2. **How is a test scenario different from a test case?**
   A scenario says *what* to test. A test case says *how*: steps, data, expected result and status. One scenario gives many test cases.

3. **What is positive and negative testing? Give a Gmail example.**
   Positive uses valid input (correct password opens the inbox, TS11). Negative uses invalid input (blank password gives "Enter a password", TS13).

4. **Which technique is used here, black-box or white-box?**
   Black-box, because only the visible behaviour of the login page is used and no source code is seen.

5. **Why is the Gmail login treated as two screens?**
   Gmail asks for the email first and checks it, then asks for the password. So email-screen and password-screen scenarios are listed separately.

6. **Name two security scenarios for a login page.**
   SQL injection in the email field (TS28) and a script in the email field to check XSS (TS29). Others: password masked, HTTPS, no access via Back button after logout.

7. **Why should you test the password in the wrong case (TS14)?**
   Passwords are case-sensitive but emails are not (TS08). A tester must check both rules.

8. **What is a non-functional scenario? Give an example from this list.**
   One that checks a quality such as speed or compatibility, not a feature. Example: TS35, page loads in 2 to 3 seconds.

9. **How do you decide that a scenario list is complete?**
   Check that every requirement has at least one scenario, and that functional, UI, security, compatibility and performance groups are all covered, with both positive and negative cases.

10. **Why can some scenarios not be automated easily against real Gmail?**
    Google shows CAPTCHA and "This browser may not be secure" for automated logins. That is why Assignment 2 uses a simulator.
