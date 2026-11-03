# Assignment 5: Selenium WebDriver and Selenium Grid

## Aim
Installation of Selenium Grid and Selenium WebDriver (Java / Eclipse) automation tools. In this repository the tests are written in Python, and the README also gives the Java and Eclipse steps.

## Theory and Fundamentals

### What is Selenium?
Selenium is a free, open-source suite for automating web browsers. A script acts like a user: it opens a page, types, clicks and checks what is shown. It is used for **functional UI testing** and **regression testing**.

### Components
| Component | What it does |
| --- | --- |
| **Selenium WebDriver** | The main API. Your script (Python, Java, C# ...) sends commands to a real browser. |
| **Browser driver** | A small program (`chromedriver`, `msedgedriver`, `geckodriver`) that translates WebDriver commands for one browser. From Selenium 4.6, **Selenium Manager** downloads the right driver automatically. |
| **Selenium Grid** | Runs tests on remote machines and many browsers in parallel. |
| **Selenium IDE** | Browser extension that records and plays back tests (used in Assignment 9). |

### How WebDriver works
```
Test script -> WebDriver client library -> (W3C WebDriver protocol, HTTP/JSON) -> Browser driver -> Real browser
```
The W3C WebDriver protocol is a standard, so the same script style works with Chrome, Edge or Firefox.

### Selenium Grid architecture
```
Test script -> Hub (:4444) -> Node 1 (Chrome, Windows)
 (Remote                   -> Node 2 (Edge, Linux)
  WebDriver)
```
- **Hub**: receives test requests and sends each to a suitable node.
- **Node**: a machine that has a browser installed and runs the session.
- **Standalone mode**: hub and node together on one computer. **Hub and Node mode**: on separate machines.
- Grid 4 is a Java program, so **Java 11 or newer** is needed even when the tests are in Python.
- Benefits: parallel execution, cross-browser and cross-platform testing, saved time.

### Locators
A locator tells Selenium which element to use.

| Locator | Example | Notes |
| --- | --- | --- |
| ID | `By.ID, "my-text-id"` | fastest and best when unique |
| NAME | `By.NAME, "my-password"` | |
| CSS selector | `textarea[name='my-textarea']` | flexible, fast |
| XPath | `//input[@id='my-check-2']` | powerful, can walk up and down the tree |
| TAG, CLASS, LINK_TEXT | | also available |

### Waits
Pages load asynchronously, so an element may not be ready yet.
- **Implicit wait**: one global time-out for every lookup.
- **Explicit wait**: wait for one specific condition (`WebDriverWait` with `expected_conditions`). Preferred.
- **Thread.sleep / time.sleep**: fixed pause. Avoid it, because it is slow and still flaky.

### Other basics
- **Assertion**: a check that must hold (title equals "Web form").
- **Headless mode**: browser runs without a window, useful for servers and CI.
- **Remote WebDriver**: a driver object that talks to a Grid URL instead of a local browser.

## How the Code / Document Works

Folder `5_Selenium/` contains `selenium_webdriver_test.py`, `README.md` (installation steps) and `result.png` (a screenshot saved by the script).

### The test target
The official Selenium practice page `https://www.selenium.dev/selenium/web/web-form.html`. It needs internet access.

### `create_driver(browser, grid_url)`
Builds Chrome or Edge options, and decides local or Grid.

```python
if grid_url:
    # Remote WebDriver: the Grid hub picks a node that has this browser
    return webdriver.Remote(command_executor=grid_url, options=options)
...
return webdriver.Chrome(options=options)   # Selenium Manager downloads the driver
```

- If environment variable `HEADLESS=1`, it adds `--headless=new` and a window size of 1366x900 (the default headless window is too small to click everything).
- If `CHROME_BIN` is set (the Docker image), it uses that Chromium binary with `--no-sandbox` and `--disable-dev-shm-usage`.

### `run_test(driver)`
A helper `check(name, condition)` records and prints PASS or FAIL. Then eight steps run:

| Step | Action | Locator used |
| --- | --- | --- |
| 1 | `driver.get(URL)`, check title is "Web form" | |
| 2 | type into the text box, check its value | `By.ID` |
| 3 | type a password | `By.NAME` |
| 4 | type into the textarea | `By.CSS_SELECTOR` |
| 5 | choose "Two" in the drop-down with the `Select` class | `By.NAME` |
| 6 | tick the checkbox, check `is_selected()` | `By.XPATH` |
| 7 | click the submit button | `By.CSS_SELECTOR` |
| 8 | **explicit wait** for the message, check it equals "Received!" | `By.ID` |

The explicit wait and the screenshot:

```python
wait = WebDriverWait(driver, 10)
message = wait.until(EC.visibility_of_element_located((By.ID, "message")))
check("Form submitted message is 'Received!'", message.text == "Received!")
driver.save_screenshot("result.png")
```

There are 5 checks in total (title, text box, drop-down, checkbox, message).

### `__main__`
`argparse` gives two options: `--browser {chrome,edge}` and `--grid URL`. The driver is created, `run_test` is run inside `try`, and `driver.quit()` is always called in `finally`. The exit code is 0 only if all checks pass.

### The README (installation guide)
- **Part A, WebDriver in Python:** install Python, run `pip install selenium`, check with `python -c "import selenium; print(selenium.__version__)"`, install Chrome or Edge (no manual driver download).
- **Part B, Grid:** install Java 11+, download `selenium-server-<version>.jar` from the Selenium GitHub releases, then start either
  `java -jar selenium-server-<version>.jar standalone`
  or hub and node:
  `java -jar selenium-server-<version>.jar hub` and
  `java -jar selenium-server-<version>.jar node --hub http://<hub-ip>:4444`.
  The Grid console is at `http://localhost:4444/ui`.
- **Part C, Java + Eclipse:** install JDK 11+ and Eclipse IDE for Java Developers, create a **Maven Project**, add the `selenium-java` dependency (version 4.25.0 in the README) to `pom.xml`, and write:

```java
WebDriver driver = new ChromeDriver();
driver.get("https://www.selenium.dev/selenium/web/web-form.html");
System.out.println(driver.getTitle());
driver.quit();
```

For Grid in Java use `new RemoteWebDriver(new URL("http://localhost:4444"), new ChromeOptions())`.

## How to Run and Expected Output

Local browser:
```bash
cd 5_Selenium
python selenium_webdriver_test.py
python selenium_webdriver_test.py --browser edge
```

On Selenium Grid (start the Grid first, see Part B):
```bash
python selenium_webdriver_test.py --grid http://localhost:4444
python selenium_webdriver_test.py --grid http://localhost:4444 --browser edge
```

Expected output (the README shows the final line as an example):

```
Running locally on chrome
  [PASS] Page title is 'Web form'
  [PASS] Text box accepts input
  [PASS] Drop-down option 'Two' selected
  [PASS] Checkbox ticked
  [PASS] Form submitted message is 'Received!'
  Screenshot saved as result.png

Total: 5   Passed: 5   Failed: 0
```

With `--grid`, the first line is `Running on Selenium Grid: http://localhost:4444`, and the session appears in the Grid console while it runs.

### Common errors (from the README)
| Error | Fix |
| --- | --- |
| `UnsupportedClassVersionError` when starting the Grid | Java is too old. Install Java 11+ |
| `SessionNotCreatedException` | Browser and driver versions differ. Update the browser |
| `Could not start a new session ... No nodes support` | No node has that browser. Start a node or use `--browser` |
| `NoSuchElementException` | Wrong locator, or page not loaded. Use an explicit wait |

## Related Concepts and Real-World Tools

- **Test frameworks**: JUnit and TestNG (Java), pytest and unittest (Python) organise Selenium tests, give reports and run them in parallel.
- **Page Object Model**: a design pattern where each page is a class with its locators and actions, making tests easier to maintain.
- **Build tools**: Maven or Gradle (Java) manage Selenium dependencies.
- **Cloud grids**: BrowserStack, Sauce Labs and LambdaTest are hosted Grids with many real browsers.
- **Docker Selenium**: ready-made container images for hub and nodes.
- **Alternatives**: Playwright, Cypress and Puppeteer are newer tools with built-in waiting. Appium extends the WebDriver idea to mobile apps.
- **CI**: Jenkins and GitHub Actions run Selenium tests headless after each commit.

## Viva Questions

1. **What is Selenium WebDriver?**
   An API that controls a real browser from code. Scripts send commands (open, click, type) and read results from the page.

2. **Why do we need a browser driver like chromedriver?**
   It translates WebDriver commands into the browser's own language. Since Selenium 4.6, Selenium Manager downloads it automatically.

3. **What is Selenium Grid and what are the hub and node?**
   Grid runs tests on remote machines in parallel. The hub receives requests and routes them. A node has a browser and executes the session.

4. **Why is Java needed to run Grid even for Python tests?**
   The Selenium Grid server is a Java program (`selenium-server.jar`), so Java 11 or newer must be installed. The tests only connect to it by URL.

5. **What are the types of locators? Which is best?**
   ID, name, class, tag, link text, CSS selector and XPath. ID is best when it is unique, because it is fast and stable.

6. **Difference between implicit and explicit wait?**
   Implicit wait is a global time-out for all element searches. Explicit wait waits for one condition on one element (for example visible). Explicit is more precise.

7. **How does the script run on Grid instead of locally?**
   `webdriver.Remote(command_executor=grid_url, options=options)` sends commands to the hub URL, and the hub picks a node.

8. **What is headless mode?**
   The browser runs without a visible window, for servers or CI. In this script `HEADLESS=1` turns it on.

9. **What does `driver.quit()` do and why is it in `finally`?**
   It closes the browser and ends the session. In `finally` it runs even if the test raises an error, so no browser is left open.

10. **How do you set up Selenium in Java with Eclipse?**
    Install JDK and Eclipse, create a Maven project, add the `selenium-java` dependency to `pom.xml`, then write a class that creates a `ChromeDriver`, opens a URL and calls `quit()`.
