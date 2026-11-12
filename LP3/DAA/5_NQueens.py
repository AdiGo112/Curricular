# Assignment 5: N-Queens with the first queen already placed.
#
# Problem Statement:
#   Design an n-Queens matrix having the first Queen already placed;
#   use backtracking to place the remaining Queens to generate the
#   final n-queens matrix. (The first queen's row-0 column is given
#   up front; this differs from solving n-queens from scratch.)
#
# Row 0's column is given; backtracking places the rest.
#
# Time: O(N!) worst case (same branching as classic n-queens).
# Space: O(N^2) board + O(N) recursion depth.


def is_safe(board, row, col, n):
    for i in range(row):
        if board[i][col] == 'Q':
            return False

    i, j = row - 1, col - 1
    while i >= 0 and j >= 0:
        if board[i][j] == 'Q':
            return False
        i, j = i - 1, j - 1

    i, j = row - 1, col + 1
    while i >= 0 and j < n:
        if board[i][j] == 'Q':
            return False
        i, j = i - 1, j + 1

    return True


def solve(board, row, n):
    if row == n:
        return True
    for col in range(n):
        if is_safe(board, row, col, n):
            board[row][col] = 'Q'
            if solve(board, row + 1, n):
                return True
            board[row][col] = '.'  # backtrack
    return False


n = int(input("Enter value of N: "))
first_queen_col = int(input(f"Enter column for the first queen (row 0), between 0 and {n - 1}: "))

board = [['.' for _ in range(n)] for _ in range(n)]
board[0][first_queen_col] = 'Q'

if solve(board, 1, n):
    print(f"\nSolution for N = {n} with first queen at (0, {first_queen_col}):\n")
    for row in board:
        print(" ".join(row))
else:
    print("No Solution Exists")
