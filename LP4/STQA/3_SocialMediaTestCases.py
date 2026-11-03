# =========================================================
# ASSIGNMENT 3
# Test Cases in Excel Sheet for a Social Media Application
# =========================================================
#
# This program creates "SocialMedia_TestCases.xlsx" with:
#
#   Sheet 1 "Test Cases" : all test cases with steps,
#                          test data and expected result.
#                          Status column has a drop-down
#                          (Pass / Fail / Blocked / Not Run).
#   Sheet 2 "Summary"    : counts per status, calculated by
#                          Excel formulas (updates by itself
#                          when you change a status).
#
# =========================================================
# HOW TO USE
# =========================================================
#
#   pip install openpyxl
#   python 3_SocialMediaTestCases.py
#
# Open the .xlsx file, execute each test case on the app,
# then fill "Actual Result" and choose a "Status".
#
# =========================================================

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

# =========================================================
# TEST CASES
# (Module, Scenario, Pre-condition, Steps, Test Data, Expected, Priority)
# =========================================================

TEST_CASES = [
    # ---------------- Sign Up ----------------
    ("Sign Up", "Register with valid details", "App is open",
     "1. Click Sign Up\n2. Enter details\n3. Click Register",
     "Name: Adi, Email: adi@test.com, Pwd: Adi@1234", "Account created, verification mail sent", "High"),
    ("Sign Up", "Register with an already used email", "adi@test.com exists",
     "1. Click Sign Up\n2. Enter used email\n3. Click Register",
     "Email: adi@test.com", "Error 'Email already registered'", "High"),
    ("Sign Up", "Register with weak password", "App is open",
     "1. Click Sign Up\n2. Enter weak password\n3. Click Register",
     "Pwd: 12345", "Error 'Password must be 8+ chars with letter, digit, symbol'", "Medium"),
    ("Sign Up", "Register with mandatory field blank", "App is open",
     "1. Click Sign Up\n2. Leave Name blank\n3. Click Register",
     "Name: (blank)", "Error 'Name is required'", "Medium"),

    # ---------------- Login ----------------
    ("Login", "Login with valid credentials", "User is registered",
     "1. Enter email\n2. Enter password\n3. Click Login",
     "adi@test.com / Adi@1234", "Home feed is displayed", "High"),
    ("Login", "Login with wrong password", "User is registered",
     "1. Enter email\n2. Enter wrong password\n3. Click Login",
     "adi@test.com / wrong", "Error 'Incorrect password'", "High"),
    ("Login", "Login with blank fields", "App is open",
     "1. Leave fields blank\n2. Click Login", "(blank)", "Login button disabled / error shown", "Medium"),
    ("Login", "Forgot password", "User is registered",
     "1. Click Forgot password\n2. Enter email\n3. Submit",
     "adi@test.com", "Password reset link sent to email", "Medium"),

    # ---------------- Profile ----------------
    ("Profile", "Update profile picture", "User logged in",
     "1. Open profile\n2. Click Edit\n3. Upload image\n4. Save",
     "photo.jpg (2 MB)", "New picture shown on profile", "Medium"),
    ("Profile", "Upload unsupported file as picture", "User logged in",
     "1. Open profile\n2. Upload .exe file", "virus.exe", "Error 'Unsupported file type'", "Medium"),
    ("Profile", "Edit bio above max length", "User logged in",
     "1. Edit bio\n2. Enter 200 characters\n3. Save", "200-char text", "Error 'Bio max 150 characters'", "Low"),
    ("Profile", "Make account private", "User logged in",
     "1. Settings > Privacy\n2. Turn on Private account", "-", "Only followers can see posts", "High"),

    # ---------------- Posts ----------------
    ("Post", "Create post with image and caption", "User logged in",
     "1. Click New Post\n2. Select image\n3. Add caption\n4. Share",
     "beach.png, 'Holiday!'", "Post appears on profile and followers' feed", "High"),
    ("Post", "Create post without any content", "User logged in",
     "1. Click New Post\n2. Click Share without content", "-", "Share button disabled", "Medium"),
    ("Post", "Edit caption of own post", "Own post exists",
     "1. Open post\n2. Click ... > Edit\n3. Change caption\n4. Save",
     "'Holiday 2026!'", "Caption updated, marked 'Edited'", "Low"),
    ("Post", "Delete own post", "Own post exists",
     "1. Open post\n2. Click ... > Delete\n3. Confirm", "-", "Post removed from profile and feed", "High"),

    # ---------------- Like / Comment / Share ----------------
    ("Interaction", "Like a post", "User logged in, post visible",
     "1. Click heart icon", "-", "Like count +1, icon turns red", "High"),
    ("Interaction", "Unlike a post", "Post already liked",
     "1. Click heart icon again", "-", "Like count -1, icon turns outline", "Medium"),
    ("Interaction", "Add a comment", "Post visible",
     "1. Click comment\n2. Type text\n3. Post", "'Nice pic!'", "Comment shown under post", "High"),
    ("Interaction", "Post an empty comment", "Post visible",
     "1. Click comment\n2. Click Post without text", "(blank)", "Post button disabled", "Low"),
    ("Interaction", "Share a post to a friend", "Post visible",
     "1. Click Share\n2. Select friend\n3. Send", "Friend: Riya", "Post sent in Riya's messages", "Medium"),

    # ---------------- Follow / Search ----------------
    ("Follow", "Follow a public account", "User logged in",
     "1. Open profile of other user\n2. Click Follow", "User: riya_k", "Button shows 'Following', count +1", "High"),
    ("Follow", "Follow a private account", "Target account is private",
     "1. Open private profile\n2. Click Follow", "User: private_p", "Button shows 'Requested'", "Medium"),
    ("Search", "Search an existing user", "User logged in",
     "1. Click Search\n2. Type name", "riya", "Matching users listed", "High"),
    ("Search", "Search with special characters", "User logged in",
     "1. Click Search\n2. Type symbols", "@#$%", "'No results found', no crash", "Low"),

    # ---------------- Messaging / Notifications / Logout ----------------
    ("Messaging", "Send a direct message", "Both users follow each other",
     "1. Open Messages\n2. Select user\n3. Type and send", "'Hi!'", "Message delivered, shown as 'Sent'", "High"),
    ("Notifications", "Notification on new like", "User has a post",
     "1. Another user likes the post", "-", "Notification 'X liked your post' received", "Medium"),
    ("Security", "Session after logout", "User logged in",
     "1. Logout\n2. Press browser Back", "-", "Login page shown, feed not visible", "High"),
    ("Security", "Script in comment (XSS)", "Post visible",
     "1. Add comment with script", "<script>alert(1)</script>", "Shown as text, script not executed", "High"),
    ("Logout", "Logout from account", "User logged in",
     "1. Click profile menu\n2. Click Logout", "-", "Redirected to Login page", "High"),
]

HEADERS = ["TC ID", "Module", "Test Scenario", "Pre-condition", "Test Steps",
           "Test Data", "Expected Result", "Actual Result", "Status", "Priority", "Remarks"]
WIDTHS = [8, 13, 32, 24, 36, 28, 38, 22, 11, 9, 16]
STATUSES = ["Pass", "Fail", "Blocked", "Not Run"]


def build_workbook(path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Test Cases"

    thin = Side(style="thin", color="999999")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    wrap = Alignment(wrap_text=True, vertical="top")

    # ---------- title rows ----------
    ws["A1"] = "Social Media Application - Test Cases"
    ws["A1"].font = Font(size=14, bold=True)
    ws["A2"] = "Prepared by: ____________    Version: 1.0    Environment: Chrome / Android"
    ws.merge_cells("A1:K1")
    ws.merge_cells("A2:K2")

    # ---------- header ----------
    header_row = 4
    for col, (name, width) in enumerate(zip(HEADERS, WIDTHS), start=1):
        cell = ws.cell(row=header_row, column=col, value=name)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E78")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
        ws.column_dimensions[cell.column_letter].width = width

    # ---------- test case rows ----------
    for i, tc in enumerate(TEST_CASES, start=1):
        module, scenario, pre, steps, data, expected, priority = tc
        row = [f"TC{i:02d}", module, scenario, pre, steps, data, expected, "", "Not Run", priority, ""]
        r = header_row + i
        for col, value in enumerate(row, start=1):
            cell = ws.cell(row=r, column=col, value=value)
            cell.alignment = wrap
            cell.border = border

    last_row = header_row + len(TEST_CASES)

    # ---------- Status drop-down ----------
    dv = DataValidation(type="list", formula1='"' + ",".join(STATUSES) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"I{header_row + 1}:I{last_row}")

    ws.freeze_panes = ws.cell(row=header_row + 1, column=3)
    ws.auto_filter.ref = f"A{header_row}:K{last_row}"

    # ---------- Summary sheet ----------
    summary = wb.create_sheet("Summary")
    summary["A1"] = "Test Execution Summary"
    summary["A1"].font = Font(size=14, bold=True)
    status_range = f"'Test Cases'!I{header_row + 1}:I{last_row}"
    summary.append([])
    summary.append(["Status", "Count"])
    for status in STATUSES:
        summary.append([status, f'=COUNTIF({status_range},"{status}")'])
    summary.append(["Total", f"=COUNTA({status_range})"])
    summary.append(["Pass %", '=IF(B8=0,0,B4/B8)'])
    summary["B9"].number_format = "0.0%"
    for cell in summary[3]:
        cell.font = Font(bold=True)
    summary.column_dimensions["A"].width = 14

    wb.save(path)


if __name__ == "__main__":
    out = "SocialMedia_TestCases.xlsx"
    build_workbook(out)
    print(f"Created {out} with {len(TEST_CASES)} test cases.")
