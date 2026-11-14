def safe(cols, row, col):
    return all(c != col and abs(c - col) != row - r for r, c in enumerate(cols[:row]))


def solve(cols, row):
    if row == len(cols):
        return True
    for col in range(len(cols)):
        if safe(cols, row, col):
            cols[row] = col
            if solve(cols, row + 1):
                return True
    return False


n = int(input("Enter N: "))
cols = [0] * n
cols[0] = int(input(f"Column of the first queen (0 to {n - 1}): "))

if solve(cols, 1):
    for col in cols:
        print(" ".join("Q" if c == col else "." for c in range(n)))
else:
    print("No solution")
