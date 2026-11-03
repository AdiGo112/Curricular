# =========================================================
# SELENIUM WEBDRIVER REGRESSION SUITE
# =========================================================
#
# Re-runs the main user flows of TaskTrack in a real
# browser after every code change (regression testing).
#
# The script starts the Flask app by itself on port 5001,
# so you do NOT need to run app.py separately.
#
# RUN:
#   pip install selenium flask
#   python test_selenium_regression.py
#
# OPTIONS (environment variables):
#   BROWSER=edge         use Edge instead of Chrome
#   HEADLESS=1           run without opening a window
#
# OUTPUT: test_report_selenium.txt
#
# =========================================================

import os
import sys
import threading
import unittest

from selenium import webdriver
from selenium.webdriver.common.by import By
from werkzeug.serving import make_server

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app as webapp
from report import run_and_report

BASE = "http://127.0.0.1:5001"


def make_driver():
    headless = os.environ.get("HEADLESS") == "1"
    if os.environ.get("BROWSER", "chrome").lower() == "edge":
        opts = webdriver.EdgeOptions()
        if headless:
            opts.add_argument("--headless=new")
        return webdriver.Edge(options=opts)
    opts = webdriver.ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
    return webdriver.Chrome(options=opts)   # Selenium Manager downloads the driver


class TaskTrackRegression(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = make_server("127.0.0.1", 5001, webapp.app)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.driver = make_driver()
        cls.driver.implicitly_wait(3)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        cls.server.shutdown()

    def setUp(self):
        webapp.users.clear()
        webapp.tasks.clear()
        self.driver.delete_all_cookies()

    # ---------- helpers ----------

    def find(self, css):
        return self.driver.find_element(By.CSS_SELECTOR, css)

    def fill(self, **fields):
        for field_id, value in fields.items():
            box = self.find("#" + field_id)
            box.clear()
            box.send_keys(value)
        self.find("#submit").click()

    def register_and_login(self, user="seluser", pwd="pass12"):
        self.driver.get(BASE + "/register")
        self.fill(username=user, password=pwd, confirm=pwd)
        self.driver.get(BASE + "/login")   # fresh page avoids stale elements
        self.fill(username=user, password=pwd)

    def add_task(self, title):
        box = self.find("#task-title")
        box.send_keys(title)
        self.find("#add-task").click()

    # ---------- regression test cases ----------

    def test_01_login_page_loads(self):
        """RT-01: Home page redirects to Login page"""
        self.driver.get(BASE)
        self.assertEqual(self.find("#heading").text, "Login")
        self.assertIn("TaskTrack", self.driver.title)

    def test_02_register_success(self):
        """RT-02: Valid registration shows success message"""
        self.driver.get(BASE + "/register")
        self.fill(username="seluser", password="pass12", confirm="pass12")
        self.assertIn("successful", self.find("#msg").text)

    def test_03_register_weak_password(self):
        """RT-03: Password without digit is rejected"""
        self.driver.get(BASE + "/register")
        self.fill(username="seluser", password="abcdefg", confirm="abcdefg")
        self.assertIn("digit", self.find("#error").text)

    def test_04_login_invalid(self):
        """RT-04: Wrong credentials show error"""
        self.driver.get(BASE + "/login")
        self.fill(username="nobody", password="wrong12")
        self.assertIn("Invalid", self.find("#error").text)

    def test_05_login_valid(self):
        """RT-05: Valid login opens My Tasks page"""
        self.register_and_login()
        self.assertEqual(self.find("#heading").text, "My Tasks")
        self.assertEqual(self.find("#user").text, "seluser")

    def test_06_add_task(self):
        """RT-06: Added task appears in the list"""
        self.register_and_login()
        self.add_task("Prepare test plan")
        self.assertEqual(self.find("#task-list .title").text, "Prepare test plan")
        self.assertEqual(self.find("#count").text, "1 task(s)")

    def test_07_blank_task_rejected(self):
        """RT-07: Blank task title shows error"""
        self.register_and_login()
        self.add_task("   ")
        self.assertIn("empty", self.find("#error").text)

    def test_08_complete_task(self):
        """RT-08: Done link marks task completed"""
        self.register_and_login()
        self.add_task("Run regression")
        self.find(".complete").click()
        self.assertIn("done", self.find(".task").get_attribute("class"))

    def test_09_delete_task(self):
        """RT-09: Delete link removes the task"""
        self.register_and_login()
        self.add_task("Temporary task")
        self.find(".delete").click()
        self.assertEqual(self.find("#count").text, "0 task(s)")

    def test_10_logout(self):
        """RT-10: Logout blocks access to tasks page"""
        self.register_and_login()
        self.find("#logout").click()
        self.driver.get(BASE + "/tasks")
        self.assertEqual(self.find("#heading").text, "Login")


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    ok = run_and_report(
        [TaskTrackRegression],
        "TaskTrack - Selenium Regression Test Report",
        os.path.join(here, "test_report_selenium.txt"),
    )
    sys.exit(0 if ok else 1)
