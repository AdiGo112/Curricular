# =========================================================
# UNIT + INTEGRATION TESTS  (White-box and Black-box)
# =========================================================
#
# White-box : tests written by looking at the code of the
#             validation functions, so every branch runs.
# Black-box : tests the app only through HTTP requests,
#             using equivalence classes and boundary values.
# Integration: full flow register -> login -> tasks -> logout.
#
# Tool: unittest (built into Python) + Flask test client
#
# RUN:  python test_unit_integration.py
# OUTPUT: test_report_unit.txt
#
# =========================================================

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app as webapp
from report import run_and_report


# =========================================================
# WHITE-BOX UNIT TESTS  (branch coverage of validators)
# =========================================================

class WhiteBoxValidation(unittest.TestCase):

    def test_username_valid(self):
        """Branch: regex matches -> no error"""
        self.assertEqual(webapp.validate_username("adi_123"), "")

    def test_username_too_short(self):
        """Branch: regex fails (length 2)"""
        self.assertNotEqual(webapp.validate_username("ab"), "")

    def test_username_special_char(self):
        """Branch: regex fails (invalid character)"""
        self.assertNotEqual(webapp.validate_username("adi@123"), "")

    def test_password_too_short(self):
        """Branch 1: len < 6"""
        self.assertIn("6 characters", webapp.validate_password("ab1"))

    def test_password_no_digit(self):
        """Branch 2: no digit"""
        self.assertIn("digit", webapp.validate_password("abcdefg"))

    def test_password_valid(self):
        """Branch 3: all checks pass"""
        self.assertEqual(webapp.validate_password("secret1"), "")

    def test_task_blank(self):
        """Branch 1: empty after strip"""
        self.assertNotEqual(webapp.validate_task("   "), "")

    def test_task_too_long(self):
        """Branch 2: more than 50 characters"""
        self.assertNotEqual(webapp.validate_task("x" * 51), "")

    def test_task_valid(self):
        """Branch 3: valid title"""
        self.assertEqual(webapp.validate_task("Buy milk"), "")


# =========================================================
# BLACK-BOX TESTS  (boundary value + equivalence classes)
# =========================================================

class BlackBoxBase(unittest.TestCase):

    def setUp(self):
        webapp.users.clear()
        webapp.tasks.clear()
        webapp.app.config["TESTING"] = True
        self.client = webapp.app.test_client()

    def register(self, user="tester", pwd="pass12", confirm=None):
        return self.client.post("/register", data={
            "username": user, "password": pwd,
            "confirm": pwd if confirm is None else confirm,
        })

    def login(self, user="tester", pwd="pass12"):
        return self.client.post("/login", data={"username": user, "password": pwd},
                                follow_redirects=True)


class BlackBoxRegister(BlackBoxBase):

    def test_username_boundary_min(self):
        """BVA: username length 3 (min) is accepted"""
        self.assertIn(b"Registration successful", self.register("abc").data)

    def test_username_boundary_max(self):
        """BVA: username length 15 (max) is accepted"""
        self.assertIn(b"Registration successful", self.register("a" * 15).data)

    def test_username_boundary_over(self):
        """BVA: username length 16 is rejected"""
        self.assertIn(b"3-15", self.register("a" * 16).data)

    def test_password_mismatch(self):
        """EP: confirm password differs -> error"""
        self.assertIn(b"do not match", self.register(confirm="other12").data)

    def test_duplicate_user_case_insensitive(self):
        """EP: same username in different case -> error"""
        self.register("tester")
        self.assertIn(b"already exists", self.register("TESTER").data)


class BlackBoxLogin(BlackBoxBase):

    def test_login_empty_fields(self):
        """EP: empty username and password"""
        self.assertIn(b"Enter username and password", self.login("", "").data)

    def test_login_wrong_password(self):
        """EP: registered user, wrong password"""
        self.register()
        self.assertIn(b"Invalid username or password", self.login(pwd="wrong12").data)

    def test_tasks_page_requires_login(self):
        """Security: /tasks without login redirects to /login"""
        r = self.client.get("/tasks")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.headers["Location"])


# =========================================================
# INTEGRATION TEST  (all modules working together)
# =========================================================

class IntegrationFlow(BlackBoxBase):

    def test_full_user_journey(self):
        """Register -> Login -> Add -> Complete -> Delete -> Logout"""
        self.register()
        self.assertIn(b"My Tasks", self.login().data)

        r = self.client.post("/tasks/add", data={"title": "Write SRS"}, follow_redirects=True)
        self.assertIn(b"Write SRS", r.data)
        self.assertIn(b"1 task(s)", r.data)

        r = self.client.get("/tasks/0/done", follow_redirects=True)
        self.assertIn(b"task done", r.data)

        r = self.client.get("/tasks/0/delete", follow_redirects=True)
        self.assertIn(b"0 task(s)", r.data)

        r = self.client.get("/logout", follow_redirects=True)
        self.assertIn(b"Login", r.data)
        self.assertEqual(self.client.get("/tasks").status_code, 302)

    def test_invalid_task_index_ignored(self):
        """Robustness: deleting a task that does not exist does not crash"""
        self.register()
        self.login()
        self.assertEqual(self.client.get("/tasks/99/delete").status_code, 302)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    ok = run_and_report(
        [WhiteBoxValidation, BlackBoxRegister, BlackBoxLogin, IntegrationFlow],
        "TaskTrack - Unit & Integration Test Report",
        os.path.join(here, "test_report_unit.txt"),
    )
    sys.exit(0 if ok else 1)
