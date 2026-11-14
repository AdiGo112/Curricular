#include <cstdlib>
#include <iostream>
#include <vector>
using namespace std;

int n;
vector<int> cols;

bool safe(int row, int col) {
    for (int r = 0; r < row; r++)
        if (cols[r] == col || abs(cols[r] - col) == row - r) return false;
    return true;
}

bool solve(int row) {
    if (row == n) return true;
    for (int col = 0; col < n; col++) {
        if (safe(row, col)) {
            cols[row] = col;
            if (solve(row + 1)) return true;
        }
    }
    return false;
}

int main() {
    cout << "Enter N: ";
    cin >> n;
    cols.assign(n, 0);
    cout << "Column of the first queen (0 to " << n - 1 << "): ";
    cin >> cols[0];

    if (!solve(1)) {
        cout << "No solution\n";
        return 0;
    }
    for (int row = 0; row < n; row++) {
        for (int col = 0; col < n; col++) cout << (cols[row] == col ? "Q " : ". ");
        cout << "\n";
    }
}
