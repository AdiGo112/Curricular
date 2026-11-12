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
#   python test_selenium_regression.py        (v1.1 -> writes the report)
#   python test_selenium_regression.py 1.0    (v1.0 -> console only)
#
# The same 12 scripts run on either build:
#   v1.0 -> 6 scripts fail = 6 bugs identified, REJECTED
#   v1.1 -> all pass = bugs fixed, nothing else broke, ACCEPTED
#
# Each docstring ends with [bug type, severity]: the class
# of bug reported if that script fails (see test_plan.md).
#
# OPTIONS (environment variables):
#   BROWSER=edge         use Edge instead of Chrome
#   HEADLESS=1           run without opening a window
#
# OUTPUT: test_report_selenium.txt for the accepted build v1.1,
#         with its exploratory session from exploratory_log.csv.
#         A v1.0 run prints its report (bugs identified) to the
#         console and does not overwrite the file.
#
# =========================================================

import csv
import os
import sys
import threading
import time
import unittest

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from werkzeug.serving import make_server

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app as webapp
from report import heading, run_and_report, table

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
    if os.environ.get("CHROME_BIN"):         # Docker image: use its Chromium (runs as root, small /dev/shm)
        opts.binary_location = os.environ["CHROME_BIN"]
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        return webdriver.Chrome(options=opts, service=webdriver.ChromeService(os.environ["CHROMEDRIVER"]))
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
        cls.server.server_close()   # free port 5001 for the next build's run

    def setUp(self):
        webapp.users.clear()
        webapp.tasks.clear()
        self.driver.delete_all_cookies()

    # ---------- helpers ----------

    def find(self, css):
        return self.driver.find_element(By.CSS_SELECTOR, css)

    def click_and_wait(self, css):
        """Click something that loads a new page, and wait until the old page is gone.
        click() returns before the next page arrives, so reading the page straight
        away can still see the OLD page (flaky on slower machines / Docker)."""
        old_page = self.find("html")
        self.find(css).click()

        def old_page_gone(_):
            try:
                old_page.is_enabled()
                return False
            except WebDriverException:     # stale element, or Chrome's "node does not belong to the
                return True                # document" error during navigation: both mean the page changed
        WebDriverWait(self.driver, 10).until(old_page_gone)

    def fill(self, **fields):
        for field_id, value in fields.items():
            box = self.find("#" + field_id)
            box.clear()
            box.send_keys(value)
        self.click_and_wait("#submit")

    def register_and_login(self, user="seluser", pwd="pass12"):
        self.driver.get(BASE + "/register")
        self.fill(username=user, password=pwd, confirm=pwd)
        self.driver.get(BASE + "/login")
        self.fill(username=user, password=pwd)

    def add_task(self, title):
        box = self.find("#task-title")
        box.send_keys(title)
        self.click_and_wait("#add-task")

    # ---------- regression test cases ----------

    def test_01_login_page_loads(self):
        """RT-01: Home page redirects to Login page [Functional, Major]"""
        self.driver.get(BASE)
        self.assertEqual(self.find("#heading").text, "Login")
        self.assertIn("TaskTrack", self.driver.title)

    def test_02_register_success(self):
        """RT-02: Valid registration shows success message [Functional, Critical]"""
        self.driver.get(BASE + "/register")
        self.fill(username="seluser", password="pass12", confirm="pass12")
        self.assertIn("successful", self.find("#msg").text)

    def test_03_register_weak_password(self):
        """RT-03: Password without digit is rejected [Validation/Input, Major]"""
        self.driver.get(BASE + "/register")
        self.fill(username="seluser", password="abcdefg", confirm="abcdefg")
        self.assertIn("digit", self.find("#error").text)

    def test_04_login_invalid(self):
        """RT-04: Wrong credentials show error [Security, Critical]"""
        self.driver.get(BASE + "/login")
        self.fill(username="nobody", password="wrong12")
        self.assertIn("Invalid", self.find("#error").text)

    def test_05_login_valid(self):
        """RT-05: Valid login opens My Tasks page [UI/Cosmetic, Trivial]"""
        self.register_and_login()
        self.assertEqual(self.find("#heading").text, "My Tasks")
        self.assertEqual(self.find("#user").text, "seluser")

    def test_06_add_task(self):
        """RT-06: Added task appears in the list [Functional, Major]"""
        self.register_and_login()
        self.add_task("Prepare test plan")
        self.assertEqual(self.find("#task-list .title").text, "Prepare test plan")
        self.assertEqual(self.find("#count").text, "1 task(s)")

    def test_07_blank_task_rejected(self):
        """RT-07: Blank task title shows error [Validation/Input, Minor]"""
        self.register_and_login()
        self.add_task("   ")
        self.assertIn("empty", self.find("#error").text)

    def test_08_complete_task(self):
        """RT-08: Done link marks task completed [Functional, Major]"""
        self.register_and_login()
        self.add_task("Run regression")
        self.click_and_wait(".complete")
        self.assertIn("done", self.find(".task").get_attribute("class"))

    def test_09_delete_task(self):
        """RT-09: Delete link removes the task [Functional, Major]"""
        self.register_and_login()
        self.add_task("Temporary task")
        self.click_and_wait(".delete")
        self.assertEqual(self.find("#count").text, "0 task(s)")

    def test_10_logout(self):
        """RT-10: Logout blocks access to tasks page [Session/State, Critical]"""
        self.register_and_login()
        self.click_and_wait("#logout")
        self.driver.get(BASE + "/tasks")
        self.assertEqual(self.find("#heading").text, "Login")

    def test_11_invalid_task_index(self):
        """RT-11: Invalid task index in the URL does not crash [Crash/Exception, Critical]"""
        self.register_and_login()
        self.driver.get(BASE + "/tasks/99/delete")
        self.assertNotIn("Internal Server Error", self.driver.page_source)
        self.assertEqual(self.find("#count").text, "0 task(s)")

    def test_12_html_in_title_escaped(self):
        """RT-12: HTML in a task title is shown as text, not run [Security, Critical]"""
        self.register_and_login()
        self.add_task("<b>hi</b>")
        self.assertEqual(self.find("#task-list .title").text, "<b>hi</b>")


def exploratory_section(here, version):
    """Report lines for the manual exploratory session on this build."""
    with open(os.path.join(here, "exploratory_log.csv"), encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["version"] == version]
    passed = sum(r["result"] == "Pass" for r in rows)
    lines = heading("4. Exploratory Testing (manual)")
    lines += ["Charter: explore Register, Tasks and Logout for 20 minutes with unusual input and navigation.",
              f"Result : {len(rows)} tests tried, {passed} passed, {len(rows) - passed} found a bug.", ""]
    lines += table(["ID", "Area", "What was tried", "What was observed", "Result", "Bug"],
                   [[r["id"], r["area"], r["tried"], r["observed"], r["result"], r["bug"] or "-"] for r in rows],
                   [5, 8, 28, 32, 6, 6])
    return lines


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    version = sys.argv[1] if len(sys.argv) > 1 else "1.1"
    if version not in ("1.0", "1.1"):
        sys.exit("usage: python test_selenium_regression.py [1.0|1.1]")
    webapp.VERSION = version
    ok, rate, verdict, section = run_and_report(
        [TaskTrackRegression], f"TaskTrack v{version} - Selenium Regression Test Report",
        exploratory_section(here, version))
    env = table(["Application", "Build", "Tool", "Browser", "Date"],
                [["TaskTrack (Flask)", f"v{version}", "Selenium WebDriver",
                  os.environ.get("BROWSER", "chrome").title(), time.strftime("%Y-%m-%d %H:%M:%S")]],
                [17, 5, 18, 7, 19])
    text = "\n".join(section[:3] + [""] + env + section[3:]) + "\n"

    if version == "1.1":   # the report file holds only the accepted build
        report_file = os.path.join(here, "test_report_selenium.txt")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\nReport written to {report_file}  ->  {verdict}")
    else:                  # v1.0: show the bugs identified, keep the report file as it is
        print(text)
    sys.exit(0 if ok else 1)
