// Assignment 3: Fractional Knapsack using a greedy method.
//
// Problem Statement:
//   Solve a fractional Knapsack problem using a greedy method.
//   Given item weights and values and a knapsack capacity, maximize the
//   total value carried, where any fraction of an item may be taken.
//
// Items can be split, so always taking the best value/weight ratio
// first never wastes capacity -- greedy is optimal here (unlike 0-1
// knapsack, where items can't be split).
//
// Time: O(n log n) for the sort by ratio. Space: O(n).

#include <iostream>
#include <vector>
#include <algorithm>
using namespace std;

struct Item { int weight, value; };

double fractionalKnapsack(vector<Item> &items, int capacity, vector<double> &fractions) {
    int n = items.size();
    fractions.assign(n, 0.0);

    vector<int> order(n);
    for (int i = 0; i < n; i++) order[i] = i;
    sort(order.begin(), order.end(), [&](int a, int b) {
        return (double)items[a].value / items[a].weight > (double)items[b].value / items[b].weight;
    });

    double totalValue = 0.0;
    int remaining = capacity;
    for (int i : order) {
        if (remaining <= 0) break;
        if (items[i].weight <= remaining) {
            fractions[i] = 1.0;
            totalValue += items[i].value;
            remaining -= items[i].weight;
        } else {
            double frac = (double)remaining / items[i].weight;
            fractions[i] = frac;
            totalValue += items[i].value * frac;
            remaining = 0;
        }
    }
    return totalValue;
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

    vector<double> fractions;
    double maxValue = fractionalKnapsack(items, capacity, fractions);

    cout << "\nItems (weight, value) and fraction taken:\n";
    for (int i = 0; i < n; i++)
        cout << "  (" << items[i].weight << ", " << items[i].value << ") -> fraction = " << fractions[i] << "\n";
    cout << "\nMaximum value = " << maxValue << "\n";
    return 0;
}
