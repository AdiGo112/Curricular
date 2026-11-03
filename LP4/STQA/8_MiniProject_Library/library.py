# =========================================================
# MINI PROJECT 8 - Library Management System
# =========================================================
#
# Platform : Python 3 (console application, any OS)
#
# Modules  :
#   Catalogue  - add books (ISBN-13 checked), search
#   Members    - register Student / Faculty members
#   Circulation- issue and return books, late fines
#
# Business rules:
#   Student : max 3 books, 14 days
#   Faculty : max 5 books, 30 days
#   Fine    : Rs 2/day for first 7 late days, Rs 5/day after,
#             maximum Rs 500 per book. Faculty pay half.
#   A member with unpaid fine cannot issue new books.
#
# RUN:  python library.py
#
# =========================================================

from datetime import date, timedelta

LIMITS = {"student": (3, 14), "faculty": (5, 30)}   # (max books, loan days)
FINE_CAP = 500


class LibraryError(Exception):
    pass


# =========================================================
# PURE FUNCTIONS (main white-box test targets)
# =========================================================

def valid_isbn13(isbn):
    """ISBN-13 check: weights 1,3,1,3...; total must be divisible by 10."""
    digits = isbn.replace("-", "")
    if len(digits) != 13 or not digits.isdigit():
        return False
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits))
    return total % 10 == 0


def calculate_fine(days_late, member_type):
    if days_late <= 0:
        return 0
    if days_late <= 7:
        fine = days_late * 2
    else:
        fine = 7 * 2 + (days_late - 7) * 5
    fine = min(fine, FINE_CAP)
    if member_type == "faculty":
        fine //= 2
    return fine


# =========================================================
# LIBRARY
# =========================================================

class Library:

    def __init__(self):
        self.books = {}      # isbn -> {"title", "author", "copies", "available"}
        self.members = {}    # id   -> {"name", "type", "loans": {isbn: due_date}, "fine"}

    # ---------- catalogue ----------
    def add_book(self, isbn, title, author, copies=1):
        if not valid_isbn13(isbn):
            raise LibraryError("Invalid ISBN-13")
        if not title.strip() or not author.strip():
            raise LibraryError("Title and author are required")
        if copies < 1:
            raise LibraryError("Copies must be at least 1")
        isbn = isbn.replace("-", "")
        if isbn in self.books:
            self.books[isbn]["copies"] += copies
            self.books[isbn]["available"] += copies
        else:
            self.books[isbn] = {"title": title.strip(), "author": author.strip(),
                                "copies": copies, "available": copies}
        return isbn

    def search(self, text):
        text = text.lower().strip()
        return [(isbn, b["title"], b["author"], b["available"]) for isbn, b in self.books.items()
                if text in b["title"].lower() or text in b["author"].lower()]

    # ---------- members ----------
    def register_member(self, member_id, name, member_type):
        member_type = member_type.lower()
        if member_type not in LIMITS:
            raise LibraryError("Member type must be student or faculty")
        if member_id in self.members:
            raise LibraryError("Member ID already exists")
        if not name.strip():
            raise LibraryError("Name is required")
        self.members[member_id] = {"name": name.strip(), "type": member_type, "loans": {}, "fine": 0}

    def _member(self, member_id):
        if member_id not in self.members:
            raise LibraryError("Member not found")
        return self.members[member_id]

    def _book(self, isbn):
        isbn = isbn.replace("-", "")
        if isbn not in self.books:
            raise LibraryError("Book not found")
        return isbn, self.books[isbn]

    # ---------- circulation ----------
    def issue_book(self, member_id, isbn, today=None):
        today = today or date.today()
        m = self._member(member_id)
        isbn, book = self._book(isbn)
        max_books, days = LIMITS[m["type"]]

        if m["fine"] > 0:
            raise LibraryError(f"Unpaid fine of Rs {m['fine']}")
        if isbn in m["loans"]:
            raise LibraryError("Member already has this book")
        if len(m["loans"]) >= max_books:
            raise LibraryError(f"Limit of {max_books} books reached")
        if book["available"] == 0:
            raise LibraryError("No copies available")

        book["available"] -= 1
        due = today + timedelta(days=days)
        m["loans"][isbn] = due
        return due

    def return_book(self, member_id, isbn, today=None):
        today = today or date.today()
        m = self._member(member_id)
        isbn, book = self._book(isbn)
        if isbn not in m["loans"]:
            raise LibraryError("This book was not issued to the member")

        due = m["loans"].pop(isbn)
        book["available"] += 1
        fine = calculate_fine((today - due).days, m["type"])
        m["fine"] += fine
        return fine

    def pay_fine(self, member_id, amount):
        m = self._member(member_id)
        if amount <= 0 or amount > m["fine"]:
            raise LibraryError(f"Amount must be between 1 and {m['fine']}")
        m["fine"] -= amount
        return m["fine"]


# =========================================================
# CONSOLE MENU
# =========================================================

def main():  # pragma: no cover  (interactive menu, tested manually: see test_plan.md)
    lib = Library()
    lib.add_book("978-0-13-468599-1", "The Pragmatic Programmer", "Hunt and Thomas", 2)
    lib.add_book("978-0-596-52068-7", "Head First Python", "Paul Barry", 1)
    lib.register_member("S101", "Aditya", "student")
    lib.register_member("F201", "Prof. Kulkarni", "faculty")

    menu = """
========== LIBRARY MENU ==========
1. Add book          5. Return book
2. Search book       6. Pay fine
3. Register member   7. Member details
4. Issue book        0. Exit
"""
    while True:
        print(menu)
        choice = input("Enter choice: ").strip()
        try:
            if choice == "1":
                isbn = lib.add_book(input("ISBN-13: "), input("Title: "), input("Author: "),
                                    int(input("Copies: ")))
                print("Book added:", isbn)
            elif choice == "2":
                for row in lib.search(input("Title/author contains: ")) or [("-", "No books found", "", "")]:
                    print(*row, sep=" | ")
            elif choice == "3":
                lib.register_member(input("Member ID: "), input("Name: "), input("Type (student/faculty): "))
                print("Member registered")
            elif choice == "4":
                print("Issued. Due date:", lib.issue_book(input("Member ID: "), input("ISBN: ")))
            elif choice == "5":
                mid, isbn = input("Member ID: "), input("ISBN: ")
                late = int(input("Days late (0 if on time): ") or 0)
                due = lib.members.get(mid, {}).get("loans", {}).get(isbn.replace("-", ""))
                today = due + timedelta(days=late) if due else None
                print("Returned. Fine: Rs", lib.return_book(mid, isbn, today))
            elif choice == "6":
                print("Remaining fine: Rs", lib.pay_fine(input("Member ID: "), int(input("Amount: "))))
            elif choice == "7":
                m = lib._member(input("Member ID: "))
                print(f"{m['name']} ({m['type']}), books: {len(m['loans'])}, fine: Rs {m['fine']}")
                for isbn, due in m["loans"].items():
                    print(f"  {lib.books[isbn]['title']} - due {due}")
            elif choice == "0":
                print("Goodbye")
                break
            else:
                print("Invalid choice")
        except (LibraryError, ValueError) as e:
            print("Error:", e)


if __name__ == "__main__":  # pragma: no cover
    main()
