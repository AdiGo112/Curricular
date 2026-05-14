# N-Queens Problem
# 1. Backtracking Approach
# 2. Branch and Bound Approach


# FUNCTION TO PRINT BOARD

def print_board(board, n):
    for i in range(n):
        for j in range(n):
            print(board[i][j], end=" ")
        print()
    print()


# 1. BACKTRACKING APPROACH

# Function to check safe position
def is_safe_backtracking(board, row, col, n):

    # Check left side of row
    for i in range(col):

        if board[row][i] == 'Q':
            return False

    # Check upper diagonal
    i = row
    j = col

    while i >= 0 and j >= 0:

        if board[i][j] == 'Q':
            return False

        i -= 1
        j -= 1

    # Check lower diagonal
    i = row
    j = col

    while i < n and j >= 0:

        if board[i][j] == 'Q':
            return False

        i += 1
        j -= 1

    return True


# Recursive function
def solve_backtracking(board, col, n):

    # Base Case
    if col == n:

        print("Solution Found:\n")

        print_board(board, n)

        return True

    # Try every row
    for row in range(n):

        # Check safe position
        if is_safe_backtracking(
            board,
            row,
            col,
            n
        ):

            # Place queen
            board[row][col] = 'Q'

            # Recursive call
            if solve_backtracking(
                board,
                col + 1,
                n
            ):

                return True

            # Backtracking
            board[row][col] = '.'

    return False


# 2. BRANCH AND BOUND APPROACH

# Function to check safe position
def is_safe_branch_bound(board,
                         row,
                         col,
                         left_row,
                         n):

    # Check row
    if left_row[row]:
        return False

    # Check upper diagonal
    i = row
    j = col

    while i >= 0 and j >= 0:

        if board[i][j] == 'Q':
            return False

        i -= 1
        j -= 1

    # Check lower diagonal
    i = row
    j = col

    while i < n and j >= 0:

        if board[i][j] == 'Q':
            return False

        i += 1
        j -= 1

    return True


# Recursive function
def solve_branch_bound(board,
                       col,
                       left_row,
                       n):

    # Base Case
    if col == n:

        print("Solution Found:\n")

        print_board(board, n)

        return True

    # Try every row
    for row in range(n):

        # Check safe position
        if is_safe_branch_bound(
            board,
            row,
            col,
            left_row,
            n
        ):

            # Place queen
            board[row][col] = 'Q'

            # Mark row
            left_row[row] = 1

            # Recursive call
            if solve_branch_bound(
                board,
                col + 1,
                left_row,
                n
            ):

                return True

            # Backtracking
            board[row][col] = '.'

            left_row[row] = 0

    return False


# DRIVER CODE
# Take input from user
n = int(input("Enter value of N: "))


# ---------- Backtracking ----------
print("\nBacktracking Approach \n")
board1 = [['.' for _ in range(n)]
          for _ in range(n)]

if not solve_backtracking(board1, 0, n):

    print("No Solution Exists")


# ---------- Branch and Bound ----------
print("\nBranch and Bound Approach \n")
board2 = [['.' for _ in range(n)]
          for _ in range(n)]

left_row = [0] * n

if not solve_branch_bound(
    board2,
    0,
    left_row,
    n
):

    print("No Solution Exists")