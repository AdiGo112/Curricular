#include <iostream>
#include <vector>

using namespace std;

int N = 4;

vector<vector<int>> board(N, vector<int>(N, 0));

// Check if queen placement is safe
bool isSafe(int row, int col) {

    // Check upper column
    for (int i = 0; i < row; i++) {

        if (board[i][col])
            return false;
    }

    // Check upper left diagonal
    for (int i = row - 1, j = col - 1;
         i >= 0 && j >= 0;
         i--, j--) {

        if (board[i][j])
            return false;
    }

    // Check upper right diagonal
    for (int i = row - 1, j = col + 1;
         i >= 0 && j < N;
         i--, j++) {

        if (board[i][j])
            return false;
    }

    return true;
}

// Backtracking Function
bool solve(int row) {

    // All queens placed
    if (row == N)
        return true;

    for (int col = 0; col < N; col++) {

        if (isSafe(row, col)) {

            // Place queen
            board[row][col] = 1;

            // Recur for next row
            if (solve(row + 1))
                return true;

            // Backtrack
            board[row][col] = 0;
        }
    }

    return false;
}

// Print board
void printBoard() {

    for (auto row : board) {

        for (int cell : row) {

            if (cell)
                cout << "Q ";
            else
                cout << ". ";
        }

        cout << endl;
    }
}

int main() {

    if (solve(0))
        printBoard();
    else
        cout << "No Solution\n";

    return 0;
}