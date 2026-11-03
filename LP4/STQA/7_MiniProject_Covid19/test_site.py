# =========================================================
# FUNCTIONAL TESTS for the running COVID-19 PHP site
# =========================================================
#
# Runs the functional test cases from README.md through real
# HTTP requests (with cookies, like a browser).
#
# RUN (site must be running, e.g. XAMPP or Docker):
#   python test_site.py                          default http://localhost:8081
#   COVID_URL=http://localhost/covid19 python test_site.py
#
# =========================================================

import http.cookiejar
import os
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("COVID_URL", "http://localhost:8081").rstrip("/")


class Browser:
    def __init__(self):
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def get(self, path):
        with self.opener.open(BASE + path, timeout=15) as r:
            return r.geturl(), r.read().decode("utf-8", errors="replace")

    def post(self, path, **form):
        data = urllib.parse.urlencode(form).encode()
        with self.opener.open(BASE + path, data=data, timeout=15) as r:
            return r.geturl(), r.read().decode("utf-8", errors="replace")


def registration(user, **overrides):
    form = {"full_name": "Test User", "username": user, "email": f"{user}@test.com", "phone": "9876543210",
            "age": "21", "pincode": "411001", "vaccinated": "Dose 2", "password": "Covid@2026", "confirm": "Covid@2026"}
    form.update(overrides)
    return form


results = []


def case(tc, title, condition):
    results.append(condition)
    print(f"{tc:5} {'PASS' if condition else 'FAIL'}  {title}")


user = "tester" + secrets.token_hex(3)          # unique, so the tests can be re-run
b = Browser()

url, html = b.get("/index.php")
case("TC01", "Home page loads with statistics and comments", "State-wise Statistics" in html and "Comments" in html)

url, html = b.post("/register.php", **registration(user))
case("TC02", "Valid registration redirects to login", url.endswith("login.php") and "Registration successful" in html)

url, html = b.post("/register.php", **registration("bad" + user[-6:], phone="12345"))
case("TC04", "Server rejects invalid phone (regex)", "10-digit Indian mobile" in html)

url, html = b.post("/register.php", **registration("mm" + user[-6:], confirm="Other@2026"))
case("TC05", "Password mismatch rejected", "Passwords do not match" in html)

url, html = b.post("/register.php", **registration(user, email="other@test.com"))
case("TC06", "Duplicate username rejected", "already registered" in html)

url, html = b.post("/login.php", username=user, password="Wrong@2026")
case("TC09", "Wrong password rejected", "Invalid username or password" in html)

url, html = b.post("/login.php", username="' OR '1'='1", password="' OR '1'='1")
case("TC10", "SQL injection on login fails", "Invalid username or password" in html)

anon = Browser()
url, html = anon.post("/comment.php", comment="anonymous spam")
case("TC13", "Comment without login redirected to login", url.endswith("login.php"))

url, html = b.post("/login.php", username=user, password="Covid@2026")
case("TC08", "Valid login shows greeting and comment box", f"Hi, {user}" in html and "Post Comment" in html)

text = f"Vaccination camp at Aundh on Sunday ({user})"
url, html = b.post("/comment.php", comment=text)
case("TC11", "Comment is posted and shown", text in html)

url, html = b.post("/comment.php", comment="<script>alert(1)</script>")
case("TC12", "XSS comment rejected by regex, never rendered", "<script>alert(1)" not in html and "not allowed" in html)

url, html = b.get("/logout.php")
case("TC14", "Logout ends session", "Post Comment" not in html and "Login" in html)

print(f"\n{sum(results)}/{len(results)} functional test cases passed against {BASE}")
sys.exit(0 if all(results) else 1)
