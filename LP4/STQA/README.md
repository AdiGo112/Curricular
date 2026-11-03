# STQA: Software Testing and Quality Assurance (410245(D))

```bash
pip install -r LP4/STQA/requirements.txt
python LP4/STQA/run_all.py          # runs every test suite (Selenium headless)
```

| # | Assignment | File |
| --- | --- | --- |
| 1 | Test scenarios for the Gmail login page | `1_GmailTestScenarios.md` |
| 2 | Gmail login test scenarios, executed | `2_GmailLoginTest.py` |
| 3 | Test cases in an Excel sheet (social media app) | `3_SocialMediaTestCases.py` → `SocialMedia_TestCases.xlsx` |
| 4 | Defect report | `4_DefectReport.md` |
| 5 | Selenium WebDriver + Grid | `5_Selenium/` |
| 6 | Software Requirements Specification | `6_SRS_TaskTrack.md` |
| 7 | Mini project: COVID-19 website (HTML, CSS, JS, PHP, MySQL) + regex test cases | `7_MiniProject_Covid19/` |
| 8 | Mini project: test plan, black/white-box, unit + integration, test report | `8_MiniProject_Library/` |
| 9 | Mini project: web app, test plan, Selenium WebDriver + IDE regression, exploratory testing | `9_MiniProject_TestIntegration/` |

## Docker

Everything (Python, headless Chromium, Node.js, PHP + Apache, MySQL) runs in containers, so nothing has to be installed except Docker Desktop.

```bash
cd LP4/STQA

docker compose up --build -d covid-web tasktrack
#   COVID-19 site (Mini Project 7, PHP + MySQL) -> http://localhost:8081
#   TaskTrack     (Mini Project 9, Flask)       -> http://localhost:5000

docker compose run --rm tests
#   every test suite, plus the 12 functional test cases against the live PHP site

docker compose down -v          # stop and delete the database
```

Only the test runner (no PHP site): `docker build -t stqa . && docker run --rm stqa`

| Container | Image | Purpose |
| --- | --- | --- |
| `covid-db` | `mysql:8.4` | Loads `database.sql` on first start |
| `covid-web` | `php:8.3-apache` + mysqli | COVID-19 portal |
| `tasktrack` | STQA image | TaskTrack Flask app |
| `tests` | STQA image (Python, Chromium, Node.js) | `run_all.py` |
