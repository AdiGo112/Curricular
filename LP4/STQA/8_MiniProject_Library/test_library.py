# =========================================================
# TEST SUITE - Library Management System
# =========================================================
#
#   WhiteBox*     : written from the code, so every branch of
#                   valid_isbn13() and calculate_fine() runs
#   BlackBox*     : written from the requirements only, using
#                   Equivalence Partitioning (EP) and
#                   Boundary Value Analysis (BVA)
#   Integration   : modules working together
#
# Tools: unittest (runner) + coverage.py (white-box coverage)
#
# RUN:  python run_tests.py      (tests + coverage + report)
#   or  python -m unittest -v test_library
#
# =========================================================

import unittest
from datetime import date, timedelta

from library import Library, LibraryError, calculate_fine, valid_isbn13

ISBN_A = "978-0-13-468599-1"
ISBN_B = "978-0-596-52068-7"
ISBN_C = "9780262033848"
ISBN_D = "9781492056355"
TODAY = date(2026, 11, 1)


# =========================================================
# WHITE-BOX UNIT TESTS
# =========================================================

class WhiteBoxISBN(unittest.TestCase):

    def test_valid_with_hyphens(self):
        """Path: correct length, digits, checksum OK"""
        self.assertTrue(valid_isbn13(ISBN_A))

    def test_wrong_length(self):
        """Branch: len != 13"""
        self.assertFalse(valid_isbn13("978013468599"))

    def test_non_digit(self):
        """Branch: not isdigit()"""
        self.assertFalse(valid_isbn13("97801346859X1"))

    def test_bad_checksum(self):
        """Branch: total % 10 != 0"""
        self.assertFalse(valid_isbn13("9780134685992"))


class WhiteBoxFine(unittest.TestCase):

    def test_on_time(self):
        """Branch: days_late <= 0"""
        self.assertEqual(calculate_fine(0, "student"), 0)

    def test_first_week(self):
        """Branch: 1-7 days at Rs 2"""
        self.assertEqual(calculate_fine(7, "student"), 14)

    def test_after_first_week(self):
        """Branch: > 7 days, Rs 5 after day 7"""
        self.assertEqual(calculate_fine(8, "student"), 19)

    def test_cap(self):
        """Branch: min() cap at Rs 500"""
        self.assertEqual(calculate_fine(200, "student"), 500)

    def test_faculty_half(self):
        """Branch: faculty pays half"""
        self.assertEqual(calculate_fine(8, "faculty"), 9)


# =========================================================
# BLACK-BOX TESTS
# =========================================================

class BlackBoxBase(unittest.TestCase):

    def setUp(self):
        self.lib = Library()
        for isbn in (ISBN_A, ISBN_B, ISBN_C, ISBN_D):
            self.lib.add_book(isbn, "Book " + isbn.replace("-", "")[-4:], "Author", 2)
        self.lib.register_member("S1", "Asha", "student")
        self.lib.register_member("F1", "Prof. Rao", "faculty")


class BlackBoxCatalogue(BlackBoxBase):

    def test_add_invalid_isbn(self):
        """EP: invalid ISBN rejected"""
        with self.assertRaises(LibraryError):
            self.lib.add_book("1234567890123", "X", "Y")

    def test_add_zero_copies(self):
        """BVA: copies = 0 rejected (minimum is 1)"""
        with self.assertRaises(LibraryError):
            self.lib.add_book("9780306406157", "X", "Y", 0)

    def test_add_existing_increases_copies(self):
        """EP: adding same ISBN adds copies"""
        self.lib.add_book(ISBN_A, "Same", "Same", 3)
        self.assertEqual(self.lib.books["9780134685991"]["copies"], 5)

    def test_add_blank_title(self):
        """EP: blank title rejected"""
        with self.assertRaises(LibraryError):
            self.lib.add_book("9780306406157", "   ", "Y")

    def test_search_case_insensitive(self):
        """EP: search ignores case"""
        self.assertEqual(len(self.lib.search("BOOK 5991")), 1)


class BlackBoxMembers(BlackBoxBase):

    def test_invalid_member_type(self):
        """EP: type other than student/faculty rejected"""
        with self.assertRaises(LibraryError):
            self.lib.register_member("X1", "Guest", "visitor")

    def test_blank_name(self):
        """EP: blank name rejected"""
        with self.assertRaises(LibraryError):
            self.lib.register_member("S9", "  ", "student")

    def test_duplicate_member(self):
        """EP: duplicate ID rejected"""
        with self.assertRaises(LibraryError):
            self.lib.register_member("S1", "Other", "student")


class BlackBoxCirculation(BlackBoxBase):

    def test_student_due_date(self):
        """Student loan is 14 days"""
        self.assertEqual(self.lib.issue_book("S1", ISBN_A, TODAY), TODAY + timedelta(days=14))

    def test_student_limit_boundary(self):
        """BVA: 3rd book allowed, 4th refused for student"""
        for isbn in (ISBN_A, ISBN_B, ISBN_C):
            self.lib.issue_book("S1", isbn, TODAY)
        with self.assertRaises(LibraryError):
            self.lib.issue_book("S1", ISBN_D, TODAY)

    def test_no_copies_left(self):
        """BVA: available = 0 refused"""
        self.lib.register_member("S2", "Ravi", "student")
        self.lib.register_member("S3", "Neha", "student")
        self.lib.issue_book("S1", ISBN_A, TODAY)
        self.lib.issue_book("S2", ISBN_A, TODAY)
        with self.assertRaises(LibraryError):
            self.lib.issue_book("S3", ISBN_A, TODAY)

    def test_return_on_due_date(self):
        """BVA: return on due date -> no fine"""
        due = self.lib.issue_book("S1", ISBN_A, TODAY)
        self.assertEqual(self.lib.return_book("S1", ISBN_A, due), 0)

    def test_return_one_day_late(self):
        """BVA: 1 day late -> Rs 2"""
        due = self.lib.issue_book("S1", ISBN_A, TODAY)
        self.assertEqual(self.lib.return_book("S1", ISBN_A, due + timedelta(days=1)), 2)

    def test_return_not_issued(self):
        """EP: returning a book not issued is an error"""
        with self.assertRaises(LibraryError):
            self.lib.return_book("S1", ISBN_A, TODAY)

    def test_same_book_twice(self):
        """EP: member cannot hold two copies of the same book"""
        self.lib.issue_book("S1", ISBN_A, TODAY)
        with self.assertRaises(LibraryError):
            self.lib.issue_book("S1", ISBN_A, TODAY)

    def test_unknown_book(self):
        """EP: unknown ISBN cannot be issued"""
        with self.assertRaises(LibraryError):
            self.lib.issue_book("S1", "9780306406157", TODAY)

    def test_unknown_member(self):
        """EP: unknown member cannot issue"""
        with self.assertRaises(LibraryError):
            self.lib.issue_book("Z9", ISBN_A, TODAY)


# =========================================================
# INTEGRATION TESTS
# =========================================================

class Integration(BlackBoxBase):

    def test_fine_blocks_issue_until_paid(self):
        """Issue -> late return -> blocked -> pay fine -> issue allowed"""
        due = self.lib.issue_book("S1", ISBN_A, TODAY)
        fine = self.lib.return_book("S1", ISBN_A, due + timedelta(days=10))
        self.assertEqual(fine, 29)
        with self.assertRaises(LibraryError):
            self.lib.issue_book("S1", ISBN_B, due + timedelta(days=10))
        self.assertEqual(self.lib.pay_fine("S1", 29), 0)
        self.lib.issue_book("S1", ISBN_B, due + timedelta(days=10))

    def test_copies_restored_after_return(self):
        """Catalogue and circulation stay consistent"""
        self.lib.issue_book("F1", ISBN_C, TODAY)
        self.assertEqual(self.lib.books["9780262033848"]["available"], 1)
        self.lib.return_book("F1", ISBN_C, TODAY)
        self.assertEqual(self.lib.books["9780262033848"]["available"], 2)

    def test_overpay_rejected(self):
        """Paying more than the fine is refused"""
        due = self.lib.issue_book("S1", ISBN_A, TODAY)
        self.lib.return_book("S1", ISBN_A, due + timedelta(days=2))
        with self.assertRaises(LibraryError):
            self.lib.pay_fine("S1", 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
