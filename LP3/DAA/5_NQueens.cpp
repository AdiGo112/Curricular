// Assignment 5: N-Queens with the first queen already placed.
//
// Problem Statement:
//   Design an n-Queens matrix having the first Queen already placed;
//   use backtracking to place the remaining Queens to generate the
//   final n-queens matrix. (The first queen's row-0 column is given
//   up front; this differs from solving n-queens from scratch.)
//
// Row 0's column is given; backtracking places the rest.
//
// Time: O(N!) worst case (same branching as classic n-queens).
// Space: O(N^2) board + O(N) recursion depth.

#include <iostream>
#include <vector>
using namespace std;

int N;
vector<vector<char>> board;

bool isSafe(int row, int col) {
    for (int i = 0; i < row; i++)
        if (board[i][col] == 'Q') return false;

    for (int i = row - 1, j = col - 1; i >= 0 && j >= 0; i--, j--)
        if (board[i][j] == 'Q') return false;

    for (int i = row - 1, j = col + 1; i >= 0 && j < N; i--, j++)
        if (board[i][j] == 'Q') return false;

    return true;
}

bool solve(int row) {
    if (row == N) return true;
    for (int col = 0; col < N; col++) {
        if (isSafe(row, col)) {
            board[row][col] = 'Q';
            if (solve(row + 1)) return true;
            board[row][col] = '.'; // backtrack
        }
    }
    return false;
}

int main() {
    cout << "Enter value of N: ";
    cin >> N;

    int firstQueenCol;
    cout << "Enter column for the first queen (row 0), between 0 and " << (N - 1) << ": ";
    cin >> firstQueenCol;

    board.assign(N, vector<char>(N, '.'));
    board[0][firstQueenCol] = 'Q';

    if (solve(1)) {
        cout << "\nSolution for N = " << N << " with first queen at (0, " << firstQueenCol << "):\n\n";
        for (auto &row : board) {
            for (char cell : row) cout << cell << " ";
            cout << "\n";
        }
    } else {
        cout << "No Solution Exists\n";
    }
    return 0;
}
