# Assignment 7: Mini Project - COVID-19 Information Website

## Aim
Dynamic website of COVID-19 information using HTML, CSS, JavaScript and PHP, with a MySQL database to store user account, comment and registration form details. Regular expression test cases are used for testing.

## Theory and Fundamentals

### Architecture of a dynamic website
```
Browser (HTML + CSS + JavaScript) <--HTTP--> Apache + PHP <--> MySQL database
```
- **HTML** gives the structure, **CSS** the look, **JavaScript** runs in the browser (instant checks).
- **PHP** runs on the server, reads and writes the database, and builds the HTML page. Pages are *dynamic* because the content (statistics, comments) comes from the database.
- **MySQL** stores users, comments and statistics permanently.

### Regular expressions (regex)
A regex is a pattern that describes allowed text. Useful pieces:

| Part | Meaning |
| --- | --- |
| `[A-Za-z]` | one letter |
| `[0-9]` or `\d` | one digit |
| `+`, `*`, `?` | one or more, zero or more, optional |
| `{3,14}` | between 3 and 14 repeats |
| `( ... \| ... )` | alternatives |
| `^ ... $` | start and end of the text (anchors) |
| `(?=.*[a-z])` | **lookahead**: "somewhere ahead there is a lowercase letter" (used for password rules) |
| `[^<>]` | any character except `<` and `>` |

For validation the pattern must match the **whole** value, so it is anchored: `^(?: pattern )$`.

### Why regex testing is a good test target
Each rule has valid and invalid classes and clear boundaries. So the test cases use:
- **Equivalence partitioning**: groups of inputs treated alike (phone with letters, email without `@`).
- **Boundary value analysis**: values at the edges (username length 3, 4, 15, 16; age 0, 1, 120, 121).

### Client-side vs server-side validation
- **Client-side** (JavaScript): fast feedback while typing, but the user can disable or bypass it, so it is **never trusted**.
- **Server-side** (PHP): the real check, always done again.

### Web security basics used here
| Threat | Defence in this project |
| --- | --- |
| **SQL injection** | Prepared statements (`prepare`, `bind_param`) |
| **XSS** (cross-site scripting) | regex blocks `<` and `>` in comments, and output goes through `htmlspecialchars` |
| **Plain-text passwords** | `password_hash()` and `password_verify()` |
| **Session fixation** | `session_regenerate_id(true)` after login |

## How the Code / Document Works

### File overview
| File | Role |
| --- | --- |
| `database.sql` | creates database `covid_portal` with tables `users`, `comments`, `covid_stats` |
| `config.php` | DB connection, session start, `validate()`, `h()`, page header and footer |
| `index.php` | home page: symptoms, prevention, vaccination, statistics table, comments |
| `register.php` | registration form and server-side validation |
| `login.php` / `logout.php` | account login and logout |
| `comment.php` | saves a comment of a logged-in user |
| `style.css` | responsive layout |
| `script.js` | live client-side validation |
| `regex_rules.json` | **single source** of every regex pattern and message |
| `regex_testcases.json` | 51 regex test cases |
| `test_regex.py`, `test_regex.js` | run the test cases in Python and in JavaScript |
| `test_site.py` | functional tests on the running site using HTTP |
| `Dockerfile` | PHP 8.3 + Apache with the `mysqli` extension |

### Database (`database.sql`)
- `users`: `username` and `email` are `UNIQUE`, `vaccinated` is an `ENUM('None','Dose 1','Dose 2','Booster')`, and `password VARCHAR(255)` holds the hash ("never plain text").
- `comments`: `user_id` is a **foreign key** to `users(id)` with `ON DELETE CASCADE`.
- `covid_stats`: state-wise figures. The file says these are **sample figures** to be replaced with official MoHFW data.

### One set of rules for everything (`regex_rules.json`)
Each field has a `pattern` and a `message`. Same file is read by PHP, by JavaScript and by both test runners, so rules cannot drift apart.

```json
"phone": { "pattern": "[6-9][0-9]{9}", "message": "Phone: 10-digit Indian mobile number starting with 6-9" },
"age":   { "pattern": "(1[01][0-9]|120|[1-9][0-9]?)", "message": "Age: 1-120" }
```

| Field | Pattern | Meaning |
| --- | --- | --- |
| full_name | `[A-Za-z]+( [A-Za-z]+){0,3}` | 1 to 4 words, letters only |
| username | `[A-Za-z][A-Za-z0-9_]{3,14}` | 4 to 15 characters, starts with a letter |
| email | `[A-Za-z0-9._%+-]+@...\.[A-Za-z]{2,}` | local part, `@`, domain, top-level domain of 2+ letters |
| phone | `[6-9][0-9]{9}` | 10-digit Indian mobile |
| age | `(1[01][0-9]\|120\|[1-9][0-9]?)` | 1 to 120, no leading zero |
| pincode | `[1-9][0-9]{5}` | 6 digits, not starting with 0 |
| password | four lookaheads + `{8,20}` | upper, lower, digit, special, 8 to 20 characters |
| comment | `[^<>]{1,500}` | 1 to 500 characters, no `<` or `>` |

### Server validation (`config.php`)
```php
function validate($field, $value) {
    global $RULES;
    $pattern = "/^(?:" . $RULES[$field]["pattern"] . ")$/Du";
    return preg_match($pattern, $value) ? "" : $RULES[$field]["message"];
}
```
It returns an empty string when the value is valid, otherwise the error message. Flag `D` makes `$` mean the real end of the string, so a trailing newline cannot slip through. `h()` wraps `htmlspecialchars` for safe output. The DB host, user and password come from environment variables with XAMPP defaults (`localhost`, `root`, empty), so the same code works in Docker.

### Registration flow (`register.php`)
1. Every field is trimmed (the password is not) and checked with `validate()`.
2. Confirm password must equal password, and the vaccination status must be in the allowed list.
3. If no errors, a prepared `SELECT` checks that username or email is not already registered ("Username or email already registered").
4. The password is hashed with `password_hash()`, a prepared `INSERT` saves the row, a flash message is set, and the user is redirected to `login.php`.

### Login, comment, logout
- `login.php`: blank fields show "Enter username and password". A prepared `SELECT` finds the user and `password_verify()` checks the hash. On success the session id is regenerated and `user_id` and `username` are stored. Otherwise "Invalid username or password".
- `comment.php`: if the user is not logged in or the request is not POST, redirect to login. Otherwise validate the comment with the `comment` rule, then insert with a prepared statement, or store the error in the session.
- `logout.php`: `session_destroy()` and redirect to the home page.
- `index.php`: reads statistics and the latest 20 comments (`JOIN` of comments and users). The comment box shows only if the user is logged in.

### Client-side validation (`script.js`)
```javascript
fetch("regex_rules.json").then((r) => r.json()).then((rules) => {
  ...
  if (!new RegExp("^(?:" + rule.pattern + ")$").test(value)) msg = rule.message;
```
For each `form.validate`, inputs with `data-rule` are checked on every `input` event and the message is written into the matching `.error` span. A red border class is toggled. On submit, an invalid form is stopped with `preventDefault()`. A `data-match` input checks that confirm password equals password.

### Regex test cases
`regex_testcases.json` has 51 rows of `[ID, field, input, should_match, description]`:

```json
["RT09", "username", "abc", false, "Length 3 (below minimum)"],
["RT10", "username", "a23456789012345", true, "Maximum length 15"],
["RT50", "comment", "<script>alert('xss')</script>", false, "Script tag (XSS)"]
```

Rows by field: full_name 6, username 7, email 7, phone 7, age 7, pincode 4, password 9, comment 4.

`test_regex.py` uses `re.fullmatch` and `test_regex.js` uses `new RegExp("^(?:" + ... + ")$")`. Both compare actual and expected, print a table, and write a report or exit with a status code. Running in two engines proves the pattern behaves the same in the browser (JS) and in a second language.

### Functional tests (`test_site.py`)
Uses `urllib` with a cookie jar, so it behaves like a browser. It runs 12 checks against the live site: TC01, TC02, TC04, TC05, TC06, TC09, TC10, TC13, TC08, TC11, TC12, TC14. The test user name is random (`tester` + 3 random bytes in hex), so the tests can be re-run.

## How to Run and Expected Output

### Regex tests (no PHP needed)
```bash
cd 7_MiniProject_Covid19
python test_regex.py     # also writes regex_test_report.txt
node test_regex.js
```
Expected: one line per test, then

```
Total: 51   Passed: 51   Failed: 0   Pass rate: 100.0%
```
(the Python runner prints the pass rate, the JavaScript runner prints Total / Passed / Failed).

### Running the website: XAMPP
1. Install XAMPP and start **Apache** and **MySQL**.
2. Copy the folder to `C:\xampp\htdocs\covid19`.
3. In `http://localhost/phpmyadmin` use **Import** with `database.sql`.
4. Open `http://localhost/covid19`.

If MySQL root has a password, edit the connection line in `config.php`.

### Running the website: Docker
From the `STQA` folder:
```bash
docker compose up --build -d covid-web tasktrack    # site at http://localhost:8081
docker compose run --rm tests                        # all suites including test_site.py
docker compose down -v
```

### Functional tests
```bash
python test_site.py                                   # default http://localhost:8081
COVID_URL=http://localhost/covid19 python test_site.py
```
Each line looks like `TC02  PASS  Valid registration redirects to login`, and the last line is `12/12 functional test cases passed against <URL>` if everything works.

The README lists manual cases TC01 to TC15 (including TC03 live validation, TC07 password hash in the table, TC15 responsive layout) that `test_site.py` cannot check.

## Related Concepts and Real-World Tools

- **Server stacks**: XAMPP, WAMP, LAMP. Frameworks such as Laravel (PHP), Django, Express.
- **Database tools**: phpMyAdmin, MySQL Workbench.
- **Test frameworks**: PHPUnit for PHP, Jest for JavaScript, pytest for Python.
- **Regex testers**: regex101.com explains and tests patterns.
- **Security tools**: OWASP ZAP and sqlmap check for XSS and SQL injection. OWASP Top 10 lists common web risks.
- **API / HTTP testing**: Postman, curl.
- **Browser automation**: Selenium or Playwright can drive the registration form (see Assignments 5 and 9).
- **Containers**: Docker and docker compose run PHP, MySQL and the tests in one command.
- **ReDoS**: badly written regex can be very slow on crafted input, so test patterns for performance too.

## Viva Questions

1. **What is a regular expression and why use it for validation?**
   A pattern describing allowed text. It checks format (phone, email, password) in one short rule, on both client and server.

2. **Why validate in JavaScript and also in PHP?**
   JavaScript gives quick feedback but can be bypassed. PHP checks again on the server, which is the one that is trusted.

3. **How do you keep regex rules the same in PHP, JavaScript and tests?**
   All patterns live in one file, `regex_rules.json`, which every part reads.

4. **Explain the password regex.**
   Four lookaheads require a lowercase, an uppercase, a digit and a special character, and `{8,20}` limits the length to 8 to 20 allowed characters.

5. **Which boundary values did you test?**
   Username length 3, 4, 15, 16. Password length 7, 8, 20, 21. Age 0, 1, 120, 121. Phone starting with 5 and 6.

6. **How does the site prevent SQL injection?**
   All queries that use user input are prepared statements with `bind_param`, so input is data and never SQL. The test `' OR '1'='1` fails to log in.

7. **How does the site prevent XSS?**
   The comment regex rejects `<` and `>`, and every output uses `htmlspecialchars` (`h()`), so even stored text is shown as plain text.

8. **How are passwords stored?**
   As hashes made by `password_hash()`, in `VARCHAR(255)`. Login uses `password_verify()`. Plain text is never stored.

9. **What does the `D` flag in the PHP regex do?**
   It makes `$` match only at the very end of the string, so a value with a trailing newline is not accepted by mistake.

10. **Why run the regex tests in both Python and JavaScript?**
    The browser uses the JavaScript engine and the server uses PHP. Running the same 51 cases in two engines gives confidence that the patterns behave the same way.
