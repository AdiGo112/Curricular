# =====================================================================
# Assignment 5: N-Queens with the First Queen Already Placed
# =====================================================================
#
# Problem Statement:
#   Design an n-Queens matrix having the first Queen already placed;
#   use backtracking to place the remaining Queens to generate the
#   final n-queens matrix. (The first queen's row-0 column is given
#   up front; this differs from solving n-queens from scratch.)
#
# Approach:
#   Place the first queen at the given column in row 0. Then, starting
#   from row 1, try every column in the current row; if placing a
#   queen there does not conflict with any queen placed in an earlier
#   row (same column, or either diagonal), place it and recurse to the
#   next row. If a row has no safe column left, backtrack: undo the
#   last placement and try the next option in the previous row. If no
#   placement works anywhere, report "No Solution Exists".
#
# Complexity:
#   Time : O(N!) worst case -> same branching factor as classic
#          n-queens; fixing the first queen only removes one branch
#          at the very first decision level, it does not change the
#          asymptotic bound.
#   Space: O(N^2) for the board, plus O(N) recursion depth.
#
# Likely Viva Questions:
#   Q1. How is this different from the standard n-queens problem?
#       A. The standard problem searches all columns for row 0 too;
#          here the row-0 column is fixed input, and backtracking only
#          searches rows 1 to N-1 for the remaining queens.
#   Q2. Why can the fixed first queen make "No Solution Exists" possible
#       even when N-queens is normally solvable for that N?
#       A. Some first-queen columns remove all safe completions for the
#          remaining rows, even though a different starting column
#          would have worked -- fixing it narrows the search space.
#   Q3. What is checked to decide if a position is "safe"?
#       A. No other placed queen shares its column, or either of its
#          two diagonals, with the position being tested.
# =====================================================================


# Check if a queen can be placed at (row, col) given the queens placed so far
def is_safe(board, row, col, n):

    # Check column above
    for i in range(row):
        if board[i][col] == 'Q':
            return False

    # Check upper-left diagonal
    i, j = row - 1, col - 1
    while i >= 0 and j >= 0:
        if board[i][j] == 'Q':
            return False
        i -= 1
        j -= 1

    # Check upper-right diagonal
    i, j = row - 1, col + 1
    while i >= 0 and j < n:
        if board[i][j] == 'Q':
            return False
        i -= 1
        j += 1

    return True


# BACKTRACKING FROM ROW 1 (row 0 is already fixed)
# Time complexity : O(N!) worst case -> same branching as classic n-queens
# Space complexity: O(N^2) for the board, O(N) recursion depth

def solve(board, row, n):

    # All rows filled
    if row == n:
        return True

    for col in range(n):

        if is_safe(board, row, col, n):

            # Place queen
            board[row][col] = 'Q'

            # Recur for next row
            if solve(board, row + 1, n):
                return True

            # Backtrack
            board[row][col] = '.'

    return False


def print_board(board, n):

    for row in range(n):
        print(" ".join(board[row]))


# DRIVER CODE

# Sanity check against a hand-verifiable fact, kept separate from
# whatever the user enters at the input() prompts below: classic
# 8-queens is solvable when the first queen is placed at column 0.
def run_self_test():
    sample_n = 8
    sample_first_queen_col = 0
    sample_board = [['.' for _ in range(sample_n)] for _ in range(sample_n)]
    sample_board[0][sample_first_queen_col] = 'Q'
    assert solve(sample_board, 1, sample_n) is True


run_self_test()

# Ask the user for the board size and the column where the first
# queen (row 0) is already placed.
n = int(input("Enter value of N: "))
first_queen_col = int(input(f"Enter column for the first queen (row 0), between 0 and {n - 1}: "))

board = [['.' for _ in range(n)] for _ in range(n)]
board[0][first_queen_col] = 'Q'

found = solve(board, 1, n)

if found:
    print(f"\nSolution for N = {n} with first queen at (0, {first_queen_col}):\n")
    print_board(board, n)
else:
    print("No Solution Exists")
