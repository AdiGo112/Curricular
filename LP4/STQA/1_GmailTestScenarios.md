# Assignment 1: Test Scenarios for the Gmail Login Page

## What is a Test Scenario?
A test scenario is a one-line statement of **what** to test, a feature or situation the user may meet. It does not list detailed steps (that is a test case). One scenario usually becomes several test cases.

## Application Under Test
**Gmail login page:** `https://accounts.google.com`

Gmail logs in over two screens:
1. **Email screen:** enter an email or phone, then click **Next**
2. **Password screen:** enter the password, then click **Next**

## Test Scenarios

### A. Functional: Email / Username Screen

| ID | Test Scenario | Expected Result |
| --- | --- | --- |
| TS01 | Enter a registered Gmail address and click Next | Password screen opens |
| TS02 | Enter a registered username without `@gmail.com` | Accepted, password screen opens |
| TS03 | Enter a registered phone number | Password screen (or OTP) opens |
| TS04 | Leave email blank and click Next | Error "Enter an email or phone number" |
| TS05 | Enter an unregistered email | Error "Couldn't find your Google Account" |
| TS06 | Enter an invalid format (e.g. `abc@@gmail`) | Error "Enter a valid email or phone number" |
| TS07 | Enter email with leading/trailing spaces | Spaces ignored, account found |
| TS08 | Enter email in UPPER CASE | Accepted (emails are not case-sensitive) |
| TS09 | Check the "Forgot email?" link | Account recovery page opens |
| TS10 | Check the "Create account" link | Sign-up page opens |

### B. Functional: Password Screen

| ID | Test Scenario | Expected Result |
| --- | --- | --- |
| TS11 | Enter the correct password and click Next | Inbox opens |
| TS12 | Enter a wrong password | Error "Wrong password. Try again…" |
| TS13 | Leave password blank and click Next | Error "Enter a password" |
| TS14 | Enter the password in the wrong case | Error (passwords are case-sensitive) |
| TS15 | Check "Show password" | Password becomes visible as text |
| TS16 | Check the "Forgot password?" link | Recovery flow opens |
| TS17 | Enter a wrong password many times | CAPTCHA or extra verification shown |
| TS18 | Account with 2-Step Verification on | OTP / prompt asked after the password |
| TS19 | Press Enter instead of clicking Next | Same behaviour as clicking Next |

### C. UI / Usability

| ID | Test Scenario | Expected Result |
| --- | --- | --- |
| TS20 | Check that the Google logo, title, fields and buttons are shown | All elements visible and aligned |
| TS21 | Check placeholder / label text in the fields | "Email or phone", "Enter your password" |
| TS22 | Check Tab key order | Email → Forgot email → Next … |
| TS23 | Check the language drop-down | Page text changes to the selected language |
| TS24 | Check on mobile, tablet and desktop sizes | Layout adjusts correctly |
| TS25 | Check the Help, Privacy and Terms links | Correct pages open |

### D. Security

| ID | Test Scenario | Expected Result |
| --- | --- | --- |
| TS26 | Check the password is masked by default | Shown as dots |
| TS27 | Check the page uses HTTPS | Padlock shown, URL starts with `https://` |
| TS28 | Try SQL injection (`' OR '1'='1`) in the email field | Treated as an invalid email |
| TS29 | Try a script (`<script>alert(1)</script>`) in the email field | Not executed |
| TS30 | After logout, press the browser Back button | Inbox does not open without logging in again |
| TS31 | Copy the password field text | Copy is blocked |
| TS32 | Login from a new device or location | Security alert email sent |

### E. Compatibility and Performance

| ID | Test Scenario | Expected Result |
| --- | --- | --- |
| TS33 | Open on Chrome, Firefox, Edge and Safari | Works the same on all |
| TS34 | Open on Windows, Android and iOS | Works the same on all |
| TS35 | Measure page load time | Loads within 2–3 seconds |
| TS36 | Login with a slow network | Loading indicator shown, no crash |

## Positive vs Negative Scenarios
- **Positive** (valid input, expected to succeed): TS01, TS02, TS03, TS07, TS08, TS11
- **Negative** (invalid input, expected to show an error): TS04, TS05, TS06, TS12, TS13, TS14, TS28, TS29

Assignment 2 (`2_GmailLoginTest.py`) runs the functional and security scenarios above automatically.
