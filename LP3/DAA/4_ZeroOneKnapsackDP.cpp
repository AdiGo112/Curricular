#include <iostream>
#include <vector>
using namespace std;

struct Item {
    int weight, value;
};

int knapsack(const vector<Item> &items, int capacity) {
    vector<int> dp(capacity + 1, 0);
    for (Item item : items)
        for (int c = capacity; c >= item.weight; c--)
            dp[c] = max(dp[c], dp[c - item.weight] + item.value);
    return dp[capacity];
}

int main() {
    int n, capacity;
    cout << "Enter number of items: ";
    cin >> n;

    vector<Item> items(n);
    for (int i = 0; i < n; i++) {
        cout << "Weight and value of item " << i + 1 << ": ";
        cin >> items[i].weight >> items[i].value;
    }

    cout << "Enter knapsack capacity: ";
    cin >> capacity;
    cout << "Maximum value = " << knapsack(items, capacity) << "\n";
}
