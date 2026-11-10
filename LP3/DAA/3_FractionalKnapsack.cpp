// =====================================================================
// Assignment 3: Fractional Knapsack using a Greedy Method
// =====================================================================
//
// Problem Statement:
//   Solve a fractional Knapsack problem using a greedy method.
//   Given item weights and values and a knapsack capacity, maximize the
//   total value carried, where any fraction of an item may be taken.
//
// Approach:
//   1. Compute each item's value/weight ratio.
//   2. Sort items by this ratio, descending.
//   3. Take items whole, highest ratio first, while they fit.
//   4. When the next item no longer fits whole, take just enough of it
//      (a fraction) to exactly fill the remaining capacity, then stop.
//   This greedy rule is optimal here because items are divisible: there
//   is never a reason to leave capacity unused when a higher-ratio item
//   could still fill it, even partially.
//
// Complexity (n items):
//   Time : O(n log n) -> dominated by sorting items by ratio.
//   Space: O(n)        -> storage for the order and fraction taken.
//
// Likely Viva Questions:
//   Q1. Why does greedy work for fractional knapsack but not 0-1 knapsack?
//       A. Because items can be split, filling the capacity with the
//          best ratio first never wastes capacity; any leftover space
//          can always be filled with a fraction of the next best item.
//          0-1 knapsack cannot split items, so this guarantee fails.
//   Q2. What is the greedy criterion used?
//       A. The value-to-weight ratio (value / weight) of each item.
//   Q3. When does a fractional (non-whole) amount get taken?
//       A. At most once per run: for the first item (in ratio order)
//          that does not fully fit in the remaining capacity.
// =====================================================================

#include <iostream>
#include <vector>
#include <algorithm>
#include <cmath>
#include <cassert>

using namespace std;

struct Item {

    int weight;
    int value;
};

// GREEDY FRACTIONAL KNAPSACK
// Time complexity : O(n log n) -> dominated by the sort on ratio
// Space complexity: O(n)       -> storage for the items/fractions

double fractionalKnapsack(vector<Item> &items, int capacity, vector<double> &fractions) {

    int numberOfItems = items.size();
    fractions.assign(numberOfItems, 0.0);

    // Sort the item indices by value/weight ratio, descending
    vector<int> order(numberOfItems);
    for (int i = 0; i < numberOfItems; i++)
        order[i] = i;

    sort(order.begin(), order.end(), [&](int firstIndex, int secondIndex) {

        double firstRatio = (double)items[firstIndex].value / items[firstIndex].weight;
        double secondRatio = (double)items[secondIndex].value / items[secondIndex].weight;

        return firstRatio > secondRatio;
    });

    double totalValue = 0.0;
    int remainingCapacity = capacity;

    for (int itemIndex : order) {

        if (remainingCapacity <= 0)
            break;

        if (items[itemIndex].weight <= remainingCapacity) {

            // Take the whole item
            fractions[itemIndex] = 1.0;
            totalValue += items[itemIndex].value;
            remainingCapacity -= items[itemIndex].weight;

        } else {

            // Take only a fraction of the item to fill the remaining capacity
            double fractionTaken = (double)remainingCapacity / items[itemIndex].weight;
            fractions[itemIndex] = fractionTaken;
            totalValue += items[itemIndex].value * fractionTaken;
            remainingCapacity = 0;
        }
    }

    return totalValue;
}

// Sanity check against a hand-calculated result, kept separate from
// whatever the user enters at the prompt in main().
// Classic sample: weights {10, 20, 30}, values {60, 100, 120}, capacity 50
// Expected maximum value: 240.0
void runSelfTest() {

    vector<Item> sampleItems = {
        {10, 60},
        {20, 100},
        {30, 120}
    };
    vector<double> sampleFractions;
    double sampleMaxValue = fractionalKnapsack(sampleItems, 50, sampleFractions);
    assert(abs(sampleMaxValue - 240.0) < 1e-9);
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

    int capacity;
    cout << "Enter knapsack capacity: ";
    cin >> capacity;

    vector<double> fractions;
    double maxValue = fractionalKnapsack(items, capacity, fractions);

    cout << "\nItems (weight, value) and fraction taken:\n";
    for (int i = 0; i < numberOfItems; i++)
        cout << "  (" << items[i].weight << ", " << items[i].value
             << ") -> fraction = " << fractions[i] << "\n";

    cout << "\nMaximum value = " << maxValue << "\n";

    return 0;
}
