#include <algorithm>
#include <iostream>
#include <queue>
#include <vector>
using namespace std;

struct Item {
    int weight, value;
};

struct Node {
    double bound;
    int level, value, weight;
    bool operator<(const Node &other) const { return bound < other.bound; }
};

double bound(const vector<Item> &items, int level, int value, int weight, int capacity) {
    double result = value;
    for (int i = level; i < (int)items.size(); i++) {
        int take = min(items[i].weight, capacity - weight);
        result += (double)items[i].value * take / items[i].weight;
        weight += take;
    }
    return result;
}

int knapsack(vector<Item> items, int capacity) {
    sort(items.begin(), items.end(), [](Item a, Item b) {
        return a.value * b.weight > b.value * a.weight;
    });

    int best = 0;
    priority_queue<Node> pq;
    pq.push({bound(items, 0, 0, 0, capacity), 0, 0, 0});

    while (!pq.empty()) {
        Node node = pq.top();
        pq.pop();
        if (node.bound <= best || node.level == (int)items.size()) continue;

        Item item = items[node.level];
        int level = node.level + 1;
        if (node.weight + item.weight <= capacity) {
            int value = node.value + item.value, weight = node.weight + item.weight;
            best = max(best, value);
            pq.push({bound(items, level, value, weight, capacity), level, value, weight});
        }
        pq.push({bound(items, level, node.value, node.weight, capacity), level, node.value, node.weight});
    }
    return best;
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
