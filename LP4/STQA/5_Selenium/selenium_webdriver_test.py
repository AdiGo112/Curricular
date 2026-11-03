# =========================================================
# ASSIGNMENT 5
# Selenium WebDriver + Selenium Grid (Python)
# =========================================================
#
# Automates the official Selenium practice form:
#   https://www.selenium.dev/selenium/web/web-form.html
#
# Shows the main WebDriver operations:
#   - open a browser and a URL
#   - locate elements (ID, NAME, CSS, XPATH, TAG)
#   - type text, select drop-down, tick checkbox, submit
#   - explicit wait, assertion, screenshot
#
# =========================================================
# HOW TO RUN
# =========================================================
#
# 1) Local browser (WebDriver):
#       python selenium_webdriver_test.py
#       python selenium_webdriver_test.py --browser edge
#
# 2) On Selenium Grid (start the Grid first, see README.md):
#       python selenium_webdriver_test.py --grid http://localhost:4444
#       python selenium_webdriver_test.py --grid http://localhost:4444 --browser edge
#
# =========================================================

import argparse
import os
import sys

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

URL = "https://www.selenium.dev/selenium/web/web-form.html"


def create_driver(browser, grid_url):
    options = webdriver.EdgeOptions() if browser == "edge" else webdriver.ChromeOptions()
    if os.environ.get("HEADLESS") == "1":
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1366,900")   # default headless window is too small to click everything

    if grid_url:
        # Remote WebDriver: the Grid hub picks a node that has this browser
        print(f"Running on Selenium Grid: {grid_url}")
        return webdriver.Remote(command_executor=grid_url, options=options)

    # Local WebDriver: Selenium Manager downloads the right driver automatically
    print(f"Running locally on {browser}")
    if browser == "edge":
        return webdriver.Edge(options=options)
    if os.environ.get("CHROME_BIN"):         # Docker image: use its Chromium (runs as root, small /dev/shm)
        options.binary_location = os.environ["CHROME_BIN"]
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return webdriver.Chrome(options=options, service=webdriver.ChromeService(os.environ["CHROMEDRIVER"]))
    return webdriver.Chrome(options=options)


def run_test(driver):
    results = []

    def check(name, condition):
        results.append((name, "PASS" if condition else "FAIL"))
        print(f"  [{'PASS' if condition else 'FAIL'}] {name}")

    wait = WebDriverWait(driver, 10)

    # Step 1: open page
    driver.get(URL)
    check("Page title is 'Web form'", driver.title == "Web form")

    # Step 2: text box (locate by ID)
    text_box = driver.find_element(By.ID, "my-text-id")
    text_box.send_keys("Selenium STQA")
    check("Text box accepts input", text_box.get_attribute("value") == "Selenium STQA")

    # Step 3: password (locate by NAME)
    driver.find_element(By.NAME, "my-password").send_keys("Test@123")

    # Step 4: textarea (locate by CSS selector)
    driver.find_element(By.CSS_SELECTOR, "textarea[name='my-textarea']").send_keys("Automated by Python")

    # Step 5: drop-down (Select class)
    dropdown = Select(driver.find_element(By.NAME, "my-select"))
    dropdown.select_by_visible_text("Two")
    check("Drop-down option 'Two' selected", dropdown.first_selected_option.text == "Two")

    # Step 6: checkbox (locate by XPATH)
    checkbox = driver.find_element(By.XPATH, "//input[@id='my-check-2']")
    checkbox.click()
    check("Checkbox ticked", checkbox.is_selected())

    # Step 7: submit
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # Step 8: explicit wait for result and verify
    message = wait.until(EC.visibility_of_element_located((By.ID, "message")))
    check("Form submitted message is 'Received!'", message.text == "Received!")

    driver.save_screenshot("result.png")
    print("  Screenshot saved as result.png")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Selenium WebDriver / Grid demo")
    parser.add_argument("--browser", choices=["chrome", "edge"], default="chrome")
    parser.add_argument("--grid", help="Grid URL, e.g. http://localhost:4444")
    args = parser.parse_args()

    driver = create_driver(args.browser, args.grid)
    try:
        results = run_test(driver)
    finally:
        driver.quit()

    passed = sum(1 for _, r in results if r == "PASS")
    print(f"\nTotal: {len(results)}   Passed: {passed}   Failed: {len(results) - passed}")
    sys.exit(0 if passed == len(results) else 1)
