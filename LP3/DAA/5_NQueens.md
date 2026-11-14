# Assignment 5: N-Queens with the First Queen Placed

## Problem statement
Design an n-Queens matrix having the first Queen placed. Use backtracking to
place the remaining Queens to generate the final n-queens matrix.

## Approach
Place N queens on an N x N board so that no two share a row, column or
diagonal. The queen in row 0 is given by the user; the rest are found by
backtracking, one row at a time starting from row 1.

1. For the current row, try each column.
2. If the column is safe, place the queen and recurse into the next row.
3. If the recursion fails, the loop moves on to the next column, which
   overwrites the placement. That overwrite is the backtrack.
4. Reaching row N means every queen is placed.

## Implementation notes
- The board is stored as `cols`, where `cols[row]` is the column of the queen
  in that row. One queen per row is therefore guaranteed by the structure.
- **Safety check** against each earlier row `r`:
  - same column: `cols[r] == col`
  - same diagonal: `abs(cols[r] - col) == row - r` (column distance equals row
    distance)
- No explicit "remove the queen" step is needed, because only rows before the
  current one are ever checked.
- Some first-queen positions have no solution, for example N = 4 with the
  first queen in column 0. The program prints `No solution`.

## Example
N = 6, first queen in column 1:

```
. Q . . . .
. . . Q . .
. . . . . Q
Q . . . . .
. . Q . . .
. . . . Q .
```

## Complexity
O(N!) time in the worst case, O(N) space for `cols` and the recursion.

## Viva prep

**Q: What is backtracking?**
A: Building a solution step by step and undoing the last step as soon as it
cannot lead to a valid solution.

**Q: Why place one queen per row?**
A: Two queens can never share a row, so searching row by row removes that
whole class of invalid boards.

**Q: For which N does a solution exist?**
A: For N = 1 and every N >= 4. There is none for N = 2 or 3.
