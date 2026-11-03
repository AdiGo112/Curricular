<?php
// =========================================================
// Shared setup: database connection, session, validation
// =========================================================

session_start();

// XAMPP defaults - change if your MySQL has a password
$db = new mysqli("localhost", "root", "", "covid_portal");
if ($db->connect_error) {
    die("Database connection failed: " . $db->connect_error);
}
$db->set_charset("utf8mb4");

// Same regex rules as script.js and the test runners
$RULES = json_decode(file_get_contents(__DIR__ . "/regex_rules.json"), true);

// Returns "" if valid, otherwise the error message.
// D = "$" means real end of string (no trailing newline allowed)
function validate($field, $value) {
    global $RULES;
    $pattern = "/^(?:" . $RULES[$field]["pattern"] . ")$/Du";
    return preg_match($pattern, $value) ? "" : $RULES[$field]["message"];
}

// Escape output to prevent XSS
function h($text) {
    return htmlspecialchars($text, ENT_QUOTES, "UTF-8");
}

function header_html($title) {
    $user = $_SESSION["username"] ?? null;
    echo "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>";
    echo "<meta name='viewport' content='width=device-width, initial-scale=1'>";
    echo "<title>" . h($title) . " | COVID-19 Portal</title>";
    echo "<link rel='stylesheet' href='style.css'></head><body>";
    echo "<nav><a class='brand' href='index.php'>COVID-19 Portal</a><div>";
    if ($user) {
        echo "<span>Hi, " . h($user) . "</span> <a href='logout.php'>Logout</a>";
    } else {
        echo "<a href='login.php'>Login</a> <a href='register.php'>Register</a>";
    }
    echo "</div></nav><main>";
}

function footer_html() {
    echo "</main><footer>Stay home, stay safe. Helpline: 1075</footer>";
    echo "<script src='script.js'></script></body></html>";
}
