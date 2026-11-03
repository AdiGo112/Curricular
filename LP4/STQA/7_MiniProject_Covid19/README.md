# Mini Project 7: COVID-19 Information Website (HTML, CSS, JS, PHP, MySQL)

A dynamic COVID-19 information portal. It shows symptoms, prevention, vaccination information and state-wise statistics. Users can register (form details stored in MySQL), log in, and post comments. Every input is validated with **regular expressions**, and the regex rules are tested with **51 test cases**.

## Files

| File | Purpose |
| --- | --- |
| `database.sql` | Creates the `covid_portal` database with `users`, `comments` and `covid_stats` tables |
| `config.php` | DB connection, session, `validate()` (PHP regex), XSS-safe output `h()` |
| `index.php` | Home page: information, statistics table, comments |
| `register.php` | Registration form: name, username, email, phone, age, pincode, vaccination status, password |
| `login.php` / `logout.php` | User account login and logout |
| `comment.php` | Saves a comment for the logged-in user |
| `style.css` | Responsive styling |
| `script.js` | Live client-side regex validation |
| `regex_rules.json` | **Single source** of all regex patterns, used by PHP, JS and both test runners |
| `regex_testcases.json` | 51 regex test cases |
| `test_regex.py` / `test_regex.js` | Run the test cases with the Python and JavaScript regex engines |

## Setup (XAMPP)

1. Install XAMPP from apachefriends.org and start **Apache** and **MySQL** in the Control Panel.
2. Copy this folder to `C:\xampp\htdocs\covid19`.
3. Open http://localhost/phpmyadmin, go to **Import**, choose `database.sql` and click **Go**.
4. Open http://localhost/covid19.

If your MySQL root user has a password, edit the connection line in `config.php`.

## Regular Expression Rules

| Field | Pattern | Meaning |
| --- | --- | --- |
| Full name | `[A-Za-z]+( [A-Za-z]+){0,3}` | 1–4 words, letters only, single spaces |
| Username | `[A-Za-z][A-Za-z0-9_]{3,14}` | 4–15 chars, starts with a letter |
| Email | `[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}` | local@domain.tld |
| Phone | `[6-9][0-9]{9}` | Indian mobile, 10 digits, starts with 6–9 |
| Age | `(1[01][0-9]\|120\|[1-9][0-9]?)` | 1–120, no leading zero |
| Pincode | `[1-9][0-9]{5}` | 6 digits, not starting with 0 |
| Password | `(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[@$!%*?&#])[A-Za-z0-9@$!%*?&#]{8,20}` | 8–20, upper + lower + digit + special |
| Comment | `[^<>]{1,500}` | 1–500 chars, blocks HTML tags |

Each pattern is anchored to the whole value (`^(?: … )$`). PHP also uses the `D` flag, so a trailing newline cannot slip through.

## Running the Regex Test Cases

```bash
python test_regex.py     # writes regex_test_report.txt
node test_regex.js
```

Result: **51 / 51 passed** in both Python and JavaScript. The test cases use:
- **Equivalence partitioning:** valid / invalid classes (e.g. phone with letters, email without `@`)
- **Boundary value analysis:** username length 3/4/15/16, password 7/8/20/21, age 0/1/120/121, phone starting with 5/6
- **Security cases:** `<script>` in a comment (XSS)

## Functional Test Cases

| TC | Scenario | Steps | Expected Result |
| --- | --- | --- | --- |
| TC01 | Home page loads | Open `index.php` | Info cards, statistics table and comments shown |
| TC02 | Valid registration | Fill all fields correctly, submit | Redirect to Login with "Registration successful" |
| TC03 | Live validation | Type `98765` in Mobile | Red border and phone message shown immediately |
| TC04 | Server-side validation | Disable JavaScript, submit an invalid email | Server returns the email error (JS is not trusted) |
| TC05 | Password mismatch | Different confirm password | "Passwords do not match" |
| TC06 | Duplicate account | Register the same username or email again | "Username or email already registered" |
| TC07 | Password stored safely | Check the `users` table in phpMyAdmin | Password column holds a `$2y$…` hash, not plain text |
| TC08 | Valid login | Correct username and password | Home page shows "Hi, username" and the comment box |
| TC09 | Invalid login | Wrong password | "Invalid username or password" |
| TC10 | SQL injection on login | Username `' OR '1'='1` | Login fails (prepared statements) |
| TC11 | Post comment | Logged in, type a comment, submit | Comment appears at the top of the list |
| TC12 | XSS in comment | Submit `<script>alert(1)</script>` | Rejected by regex; even if stored, output is escaped |
| TC13 | Comment without login | POST to `comment.php` while logged out | Redirected to Login |
| TC14 | Logout | Click Logout | Session ends, comment box hidden |
| TC15 | Responsive layout | Open on a phone-width screen | Cards stack, table scrolls sideways |

### Automated functional tests

`test_site.py` runs 12 of these cases (TC01, TC02, TC04–TC06, TC08–TC14) through real HTTP requests against the running site:

```bash
python test_site.py                                  # site at http://localhost:8081 (Docker)
COVID_URL=http://localhost/covid19 python test_site.py   # site on XAMPP
```

Result in Docker (`docker compose run --rm tests` from `LP4/STQA`): **12/12 passed**, and the `users` table stores bcrypt hashes (`$2y$10$…`) (TC07). TC03 (live JS feedback) and TC15 (phone layout) are checked by hand in the browser.
