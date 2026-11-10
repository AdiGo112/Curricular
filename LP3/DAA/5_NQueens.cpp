// =====================================================================
// Assignment 5: N-Queens with the First Queen Already Placed
// =====================================================================
//
// Problem Statement:
//   Design an n-Queens matrix having the first Queen already placed;
//   use backtracking to place the remaining Queens to generate the
//   final n-queens matrix. (The first queen's row-0 column is given
//   up front; this differs from solving n-queens from scratch.)
//
// Approach:
//   Place the first queen at the given column in row 0. Then, starting
//   from row 1, try every column in the current row; if placing a
//   queen there does not conflict with any queen placed in an earlier
//   row (same column, or either diagonal), place it and recurse to the
//   next row. If a row has no safe column left, backtrack: undo the
//   last placement and try the next option in the previous row. If no
//   placement works anywhere, report "No Solution Exists".
//
// Complexity:
//   Time : O(N!) worst case -> same branching factor as classic
//          n-queens; fixing the first queen only removes one branch
//          at the very first decision level, it does not change the
//          asymptotic bound.
//   Space: O(N^2) for the board, plus O(N) recursion depth.
//
// Likely Viva Questions:
//   Q1. How is this different from the standard n-queens problem?
//       A. The standard problem searches all columns for row 0 too;
//          here the row-0 column is fixed input, and backtracking only
//          searches rows 1 to N-1 for the remaining queens.
//   Q2. Why can the fixed first queen make "No Solution Exists" possible
//       even when N-queens is normally solvable for that N?
//       A. Some first-queen columns remove all safe completions for the
//          remaining rows, even though a different starting column
//          would have worked -- fixing it narrows the search space.
//   Q3. What is checked to decide if a position is "safe"?
//       A. No other placed queen shares its column, or either of its
//          two diagonals, with the position being tested.
// =====================================================================

#include <iostream>
#include <vector>
#include <cassert>

using namespace std;

int N;
vector<vector<char>> board;

// Check if a queen can be placed at (row, col) given the queens placed so far
bool isSafe(int row, int col) {

    // Check column above
    for (int i = 0; i < row; i++) {

        if (board[i][col] == 'Q')
            return false;
    }

    // Check upper-left diagonal
    for (int i = row - 1, j = col - 1; i >= 0 && j >= 0; i--, j--) {

        if (board[i][j] == 'Q')
            return false;
    }

    // Check upper-right diagonal
    for (int i = row - 1, j = col + 1; i >= 0 && j < N; i--, j++) {

        if (board[i][j] == 'Q')
            return false;
    }

    return true;
}

// BACKTRACKING FROM ROW 1 (row 0 is already fixed)
// Time complexity : O(N!) worst case -> same branching as classic n-queens
// Space complexity: O(N^2) for the board, O(N) recursion depth

bool solve(int row) {

    // All rows filled
    if (row == N)
        return true;

    for (int col = 0; col < N; col++) {

        if (isSafe(row, col)) {

            // Place queen
            board[row][col] = 'Q';

            // Recur for next row
            if (solve(row + 1))
                return true;

            // Backtrack
            board[row][col] = '.';
        }
    }

    return false;
}

void printBoard() {

    for (auto &row : board) {

        for (char cell : row)
            cout << cell << " ";

        cout << "\n";
    }
}

// Sanity check against a hand-verifiable fact, kept separate from
// whatever the user enters at the prompt in main(): classic 8-queens
// is solvable when the first queen is placed at column 0.
void runSelfTest() {

    N = 8;
    int sampleFirstQueenCol = 0;

    board.assign(N, vector<char>(N, '.'));
    board[0][sampleFirstQueenCol] = 'Q';

    bool sampleFound = solve(1);
    assert(sampleFound == true);
}

int main() {

    runSelfTest();

    // DRIVER CODE
    // Ask the user for the board size and the column where the first
    // queen (row 0) is already placed.
    cout << "Enter value of N: ";
    cin >> N;

    int firstQueenCol;
    cout << "Enter column for the first queen (row 0), between 0 and " << (N - 1) << ": ";
    cin >> firstQueenCol;

    board.assign(N, vector<char>(N, '.'));
    board[0][firstQueenCol] = 'Q';

    bool found = solve(1);

    if (found) {

        cout << "\nSolution for N = " << N << " with first queen at (0, " << firstQueenCol << "):\n\n";
        printBoard();

    } else {

        cout << "No Solution Exists\n";
    }

    return 0;
}
