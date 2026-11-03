# Assignment 5: Installing Selenium WebDriver and Selenium Grid

## Theory

| Component | What it does |
| --- | --- |
| **Selenium WebDriver** | Library that controls a real browser from code (Python, Java, …) |
| **Browser driver** | `chromedriver` / `msedgedriver` translate WebDriver commands for the browser. Selenium Manager (built into Selenium 4.6+) downloads it automatically |
| **Selenium Grid** | Runs tests on remote machines and browsers in parallel. The **Hub** receives test requests and sends each one to a **Node** that has the requested browser |
| **Selenium IDE** | Browser extension that records and plays back tests (used in the Mini Project) |

```
 Test script ──> Hub (:4444) ──> Node 1 (Chrome, Windows)
 (Remote          │
  WebDriver)      └────────────> Node 2 (Edge, Linux)
```

## Part A: Selenium WebDriver (Python)

1. Install **Python 3** from python.org and tick "Add Python to PATH".
2. Install Selenium:
   ```bash
   pip install selenium
   ```
3. Check it:
   ```bash
   python -c "import selenium; print(selenium.__version__)"
   ```
4. Install Google Chrome or Microsoft Edge. You don't need to download a driver, because Selenium Manager does it.
5. Run the test:
   ```bash
   python selenium_webdriver_test.py
   ```
   The browser opens, fills the form and submits it, and you get output like:
   ```
   [PASS] Page title is 'Web form'
   ...
   Total: 5   Passed: 5   Failed: 0
   ```

## Part B: Selenium Grid

Selenium Grid 4 is a Java program, so **Java 11 or newer** is needed even when the tests are written in Python.

1. Install Java 11+ (e.g. Eclipse Temurin JDK 17) and check it:
   ```bash
   java -version
   ```
2. Download `selenium-server-<version>.jar` from https://github.com/SeleniumHQ/selenium/releases (Assets of the latest release).
3. Start the Grid. Choose **one** mode.

   **Standalone** (hub and node on one machine, easiest):
   ```bash
   java -jar selenium-server-<version>.jar standalone
   ```

   **Hub and Node** (separate machines):
   ```bash
   # machine 1: the hub
   java -jar selenium-server-<version>.jar hub

   # machine 2 (or another terminal): a node
   java -jar selenium-server-<version>.jar node --hub http://<hub-ip>:4444
   ```
4. Open http://localhost:4444/ui in a browser. The Grid console shows the available browsers (sessions/slots).
5. Run the same test on the Grid:
   ```bash
   python selenium_webdriver_test.py --grid http://localhost:4444
   python selenium_webdriver_test.py --grid http://localhost:4444 --browser edge
   ```
   While it runs, the session appears in the Grid console.

## Part C: Java + Eclipse (if your lab requires it)

1. Install JDK 11+ and **Eclipse IDE for Java Developers**.
2. File → New → **Maven Project**, then add this to `pom.xml`:
   ```xml
   <dependency>
     <groupId>org.seleniumhq.selenium</groupId>
     <artifactId>selenium-java</artifactId>
     <version>4.25.0</version>
   </dependency>
   ```
3. Create a class with a `main` method:
   ```java
   WebDriver driver = new ChromeDriver();
   driver.get("https://www.selenium.dev/selenium/web/web-form.html");
   System.out.println(driver.getTitle());
   driver.quit();
   ```
4. For Grid, use `new RemoteWebDriver(new URL("http://localhost:4444"), new ChromeOptions())`.

## Common Errors

| Error | Fix |
| --- | --- |
| `UnsupportedClassVersionError` when starting the Grid | Java is too old. Install Java 11+ |
| `SessionNotCreatedException` | Browser and driver versions differ. Update the browser |
| `Could not start a new session ... No nodes support` | No node has that browser. Start a node, or use `--browser` |
| `NoSuchElementException` | Locator is wrong, or the page has not loaded yet. Use an explicit wait |
