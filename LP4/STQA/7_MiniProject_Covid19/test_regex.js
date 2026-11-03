// =========================================================
// REGEX TEST CASES (JavaScript runner)
// =========================================================
//
// Same test cases as test_regex.py, but run with the
// JavaScript regex engine (the one the browser uses for
// client-side validation in script.js).
//
// RUN:  node test_regex.js
//
// =========================================================

const fs = require("fs");
const path = require("path");

const rules = JSON.parse(fs.readFileSync(path.join(__dirname, "regex_rules.json")));
const cases = JSON.parse(fs.readFileSync(path.join(__dirname, "regex_testcases.json")));

let passed = 0;
for (const [id, field, value, expected, desc] of cases) {
  // same as script.js: anchor the pattern to the whole value
  const actual = new RegExp("^(?:" + rules[field].pattern + ")$").test(value);
  const ok = actual === expected;
  if (ok) passed++;
  console.log(`${id.padEnd(6)}${field.padEnd(11)}${JSON.stringify(value).slice(0, 32).padEnd(34)}` +
              `${ok ? "PASS" : "FAIL"}   ${desc}`);
}
console.log(`\nTotal: ${cases.length}   Passed: ${passed}   Failed: ${cases.length - passed}`);
process.exit(passed === cases.length ? 0 : 1);
