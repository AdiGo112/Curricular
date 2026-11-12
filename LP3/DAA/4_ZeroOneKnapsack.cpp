// Assignment 4: 0-1 Knapsack using dynamic programming.
//
// Problem Statement:
//   Solve a 0-1 Knapsack problem using dynamic programming. Given item
//   weights and values and a knapsack capacity, maximize the total
//   value carried, where each item is either taken whole or not at all.
//
// Items can't be split, so greedy by ratio can be suboptimal -- every
// (first i items, capacity c) combination is considered via a bottom-up
// table: dp[i][c] = best value using the first i items with capacity c.
//
// Time: O(n * capacity). Space: O(n * capacity).

#include <iostream>
#include <vector>
using namespace std;

struct Item { int weight, value; };

int zeroOneKnapsack(vector<Item> &items, int maxCapacity, vector<int> &chosen) {
    int n = items.size();
    vector<vector<int>> dp(n + 1, vector<int>(maxCapacity + 1, 0));

    for (int i = 1; i <= n; i++) {
        for (int c = 0; c <= maxCapacity; c++) {
            dp[i][c] = dp[i - 1][c]; // skip item i-1
            if (items[i - 1].weight <= c) {
                int taken = dp[i - 1][c - items[i - 1].weight] + items[i - 1].value;
                dp[i][c] = max(dp[i][c], taken);
            }
        }
    }

    // Backtrack: if the value changed from row i-1, item i-1 was taken.
    int c = maxCapacity;
    for (int i = n; i > 0; i--) {
        if (dp[i][c] != dp[i - 1][c]) {
            chosen.push_back(i - 1);
            c -= items[i - 1].weight;
        }
    }
    return dp[n][maxCapacity];
}

int main() {
    int n;
    cout << "Enter number of items: ";
    cin >> n;

    vector<Item> items(n);
    for (int i = 0; i < n; i++) {
        cout << "Enter weight and value of item " << (i + 1) << ": ";
        cin >> items[i].weight >> items[i].value;
    }

    int capacity;
    cout << "Enter knapsack capacity: ";
    cin >> capacity;

    vector<int> chosen;
    int maxValue = zeroOneKnapsack(items, capacity, chosen);

    cout << "\nMaximum value = " << maxValue << "\n";
    cout << "Items selected (weight, value):\n";
    for (int i : chosen)
        cout << "  (" << items[i].weight << ", " << items[i].value << ")\n";
    return 0;
}
