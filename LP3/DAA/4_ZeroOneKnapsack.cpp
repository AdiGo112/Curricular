// =====================================================================
// Assignment 4: 0-1 Knapsack using Dynamic Programming
// =====================================================================
//
// Problem Statement:
//   Solve a 0-1 Knapsack problem using dynamic programming. Given item
//   weights and values and a knapsack capacity, maximize the total
//   value carried, where each item is either taken whole or not at all.
//
// Approach:
//   Build a table dp[i][capacity] = the best value achievable using
//   only the first i items with the given capacity. For each item,
//   either skip it (dp[i][c] = dp[i-1][c]) or take it, if it fits
//   (dp[i][c] = dp[i-1][c - weight] + value). Take whichever option is
//   larger. Because items cannot be split, unlike fractional knapsack,
//   a greedy ratio-based choice can be proven suboptimal here, so every
//   combination of "first i items, capacity c" must be considered via
//   this bottom-up table. The chosen items are then recovered by
//   backtracking through the table from dp[n][capacity] to dp[0][0].
//
// Complexity (n items, capacity C):
//   Time : O(n * C) -> one table cell computed per item/capacity pair.
//   Space: O(n * C) -> the dp table itself.
//
// Likely Viva Questions:
//   Q1. Why can't the fractional knapsack's greedy approach be used here?
//       A. Items must be taken whole or not at all, so always picking
//          the best ratio first can leave leftover capacity that cannot
//          be filled optimally — a counter-example is easy to construct.
//   Q2. What does dp[i][capacity] represent?
//       A. The maximum value obtainable using only the first i items
//          with a knapsack of size "capacity".
//   Q3. How are the selected items recovered after filling the table?
//       A. By backtracking from dp[n][capacity]: if dp[i][c] differs
//          from dp[i-1][c], item (i-1) was taken, so subtract its weight
//          from c and continue to row i-1; otherwise move to row i-1
//          at the same capacity.
// =====================================================================

#include <iostream>
#include <vector>
#include <cassert>

using namespace std;

struct Item {

    int weight;
    int value;
};

// DP TABULATION
// Time complexity : O(numberOfItems * maxCapacity) -> one table cell per item/capacity pair
// Space complexity: O(numberOfItems * maxCapacity) -> the dp table itself

int zeroOneKnapsack(vector<Item> &items, int maxCapacity, vector<int> &chosenItems) {

    int numberOfItems = items.size();

    // dp[i][capacity] = best value achievable using the first i items
    // with a knapsack of the given capacity
    vector<vector<int>> dp(numberOfItems + 1, vector<int>(maxCapacity + 1, 0));

    for (int i = 1; i <= numberOfItems; i++) {

        for (int capacity = 0; capacity <= maxCapacity; capacity++) {

            // Option 1: skip this item (always available)
            dp[i][capacity] = dp[i - 1][capacity];

            // Option 2: take this item, if it fits in the current capacity
            if (items[i - 1].weight <= capacity) {

                int valueIfTaken = dp[i - 1][capacity - items[i - 1].weight] + items[i - 1].value;

                if (valueIfTaken > dp[i][capacity])
                    dp[i][capacity] = valueIfTaken;
            }
        }
    }

    // Backtrack through the table to find which items were selected
    int remainingCapacity = maxCapacity;
    for (int i = numberOfItems; i > 0; i--) {

        // If the value changed between row i and row i-1 at this capacity,
        // item (i-1) must have been taken to reach it
        if (dp[i][remainingCapacity] != dp[i - 1][remainingCapacity]) {

            chosenItems.push_back(i - 1);
            remainingCapacity -= items[i - 1].weight;
        }
    }

    return dp[numberOfItems][maxCapacity];
}

// Sanity check against a hand-calculated result, kept separate from
// whatever the user enters at the prompt in main().
// Classic sample: weights {1, 3, 4, 5}, values {1, 4, 5, 7}, capacity 7
// Expected maximum value: 9 (items with weight 3 and weight 4, value 4 + 5)
void runSelfTest() {

    vector<Item> sampleItems = {
        {1, 1},
        {3, 4},
        {4, 5},
        {5, 7}
    };
    vector<int> sampleChosenItems;
    int sampleMaxValue = zeroOneKnapsack(sampleItems, 7, sampleChosenItems);
    assert(sampleMaxValue == 9);
}

int main() {

    runSelfTest();

    // DRIVER CODE
    // Ask the user for the number of items, each item's weight and value,
    // and the knapsack's capacity.
    int numberOfItems;
    cout << "Enter number of items: ";
    cin >> numberOfItems;

    vector<Item> items(numberOfItems);
    for (int i = 0; i < numberOfItems; i++) {

        cout << "Enter weight and value of item " << (i + 1) << ": ";
        cin >> items[i].weight >> items[i].value;
    }

    int maxCapacity;
    cout << "Enter knapsack capacity: ";
    cin >> maxCapacity;

    vector<int> chosenItems;
    int maxValue = zeroOneKnapsack(items, maxCapacity, chosenItems);

    cout << "\nMaximum value = " << maxValue << "\n";
    cout << "Items selected (weight, value):\n";
    for (int itemIndex : chosenItems)
        cout << "  (" << items[itemIndex].weight << ", " << items[itemIndex].value << ")\n";

    return 0;
}
