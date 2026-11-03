# =========================================================
# ASSIGNMENT 2
# Test Scenarios for Gmail Login Page (executed)
# =========================================================
#
# The scenarios written in Assignment 1 are run here
# against a small SIMULATOR of the Gmail login flow.
#
# Why a simulator?
#   Google blocks automated logins on the real page
#   (CAPTCHA / "This browser may not be secure"), so a
#   local copy of the same rules is used to execute the
#   scenarios repeatably.
#
# Gmail login flow (2 screens):
#   1. Email screen    -> check email/phone
#   2. Password screen -> check password
#
# =========================================================
# HOW TO USE
# =========================================================
#
#   python 2_GmailLoginTest.py
#
# Each scenario prints PASS / FAIL and a summary is shown.
#
# =========================================================

import re


# =========================================================
# GMAIL LOGIN SIMULATOR (system under test)
# =========================================================

ACCOUNTS = {
    "student.stqa@gmail.com": {"password": "Test@1234", "phone": "9876543210", "two_step": False},
    "secure.user@gmail.com": {"password": "Secure#99", "phone": "9123456780", "two_step": True},
}

MAX_ATTEMPTS = 3   # after this many wrong passwords, CAPTCHA is required


class GmailLogin:

    def __init__(self):
        self.account = None
        self.wrong_attempts = 0

    # ---------- Screen 1: email / phone ----------
    def enter_email(self, text):
        text = text.strip()

        if text == "":
            return "Enter an email or phone number"

        # phone number login
        if text.isdigit():
            for email, acc in ACCOUNTS.items():
                if acc["phone"] == text:
                    self.account = email
                    return "PASSWORD_SCREEN"
            return "Couldn't find your Google Account"

        email = text.lower()
        if "@" not in email:
            email += "@gmail.com"     # username without domain

        if not re.fullmatch(r"[a-z0-9._]+@[a-z0-9-]+\.[a-z]{2,}", email):
            return "Enter a valid email or phone number"

        if email not in ACCOUNTS:
            return "Couldn't find your Google Account"

        self.account = email
        return "PASSWORD_SCREEN"

    # ---------- Screen 2: password ----------
    def enter_password(self, password):
        if self.account is None:
            return "Enter email first"
        if password == "":
            return "Enter a password"
        if self.wrong_attempts >= MAX_ATTEMPTS:
            return "CAPTCHA_REQUIRED"

        acc = ACCOUNTS[self.account]
        if password != acc["password"]:
            self.wrong_attempts += 1
            return "Wrong password. Try again or click Forgot password to reset it."

        self.wrong_attempts = 0
        return "OTP_SCREEN" if acc["two_step"] else "INBOX"


# =========================================================
# TEST SCENARIOS (from Assignment 1)
# =========================================================
#
# Each entry: (ID, description, email, password, expected)
# password = None means only the email screen is tested.
#

SCENARIOS = [
    ("TS01", "Registered Gmail address", "student.stqa@gmail.com", None, "PASSWORD_SCREEN"),
    ("TS02", "Username without @gmail.com", "student.stqa", None, "PASSWORD_SCREEN"),
    ("TS03", "Registered phone number", "9876543210", None, "PASSWORD_SCREEN"),
    ("TS04", "Blank email", "", None, "Enter an email or phone number"),
    ("TS05", "Unregistered email", "nobody123@gmail.com", None, "Couldn't find your Google Account"),
    ("TS06", "Invalid email format", "abc@@gmail", None, "Enter a valid email or phone number"),
    ("TS07", "Email with spaces around", "  student.stqa@gmail.com  ", None, "PASSWORD_SCREEN"),
    ("TS08", "Email in upper case", "STUDENT.STQA@GMAIL.COM", None, "PASSWORD_SCREEN"),
    ("TS11", "Correct password", "student.stqa@gmail.com", "Test@1234", "INBOX"),
    ("TS12", "Wrong password", "student.stqa@gmail.com", "wrong123",
     "Wrong password. Try again or click Forgot password to reset it."),
    ("TS13", "Blank password", "student.stqa@gmail.com", "", "Enter a password"),
    ("TS14", "Password in wrong case", "student.stqa@gmail.com", "test@1234",
     "Wrong password. Try again or click Forgot password to reset it."),
    ("TS18", "2-Step Verification account", "secure.user@gmail.com", "Secure#99", "OTP_SCREEN"),
    ("TS28", "SQL injection in email", "' OR '1'='1", None, "Enter a valid email or phone number"),
    ("TS29", "Script in email", "<script>alert(1)</script>", None, "Enter a valid email or phone number"),
]


def run_scenario(email, password):
    login = GmailLogin()
    result = login.enter_email(email)
    if password is None or result != "PASSWORD_SCREEN":
        return result
    return login.enter_password(password)


def run_lockout_scenario():
    # TS17: many wrong passwords -> CAPTCHA
    login = GmailLogin()
    login.enter_email("student.stqa@gmail.com")
    for _ in range(MAX_ATTEMPTS):
        login.enter_password("bad-pass")
    return login.enter_password("Test@1234")


# =========================================================
# MAIN: EXECUTE ALL SCENARIOS
# =========================================================

if __name__ == "__main__":

    print("=" * 78)
    print(" Gmail Login Page - Test Scenario Execution")
    print("=" * 78)
    print(f"{'ID':6}{'Scenario':34}{'Expected':16}{'Actual':16}Result")
    print("-" * 78)

    passed = 0
    results = [(sid, desc, exp, run_scenario(email, pwd)) for sid, desc, email, pwd, exp in SCENARIOS]
    results.append(("TS17", "Too many wrong passwords", "CAPTCHA_REQUIRED", run_lockout_scenario()))

    for sid, desc, expected, actual in results:
        status = "PASS" if actual == expected else "FAIL"
        passed += status == "PASS"
        print(f"{sid:6}{desc:34}{expected[:15]:16}{actual[:15]:16}{status}")

    total = len(results)
    print("-" * 78)
    print(f"Total: {total}   Passed: {passed}   Failed: {total - passed}")
    print("All scenarios passed." if passed == total else "Some scenarios FAILED - check above.")
    raise SystemExit(0 if passed == total else 1)
