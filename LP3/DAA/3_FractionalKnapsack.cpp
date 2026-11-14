#include <algorithm>
#include <iostream>
#include <vector>
using namespace std;

struct Item {
    int weight, value;
};

double fractionalKnapsack(vector<Item> items, int capacity) {
    sort(items.begin(), items.end(), [](Item a, Item b) {
        return a.value * b.weight > b.value * a.weight;
    });

    double total = 0;
    for (Item item : items) {
        int take = min(item.weight, capacity);
        total += (double)item.value * take / item.weight;
        capacity -= take;
    }
    return total;
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
    cout << "Maximum value = " << fractionalKnapsack(items, capacity) << "\n";
}
