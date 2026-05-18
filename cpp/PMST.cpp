#include <iostream>
#include <vector>
#include <queue>

using namespace std;

typedef pair<int, int> pii;

void prims(int V, vector<vector<pii>>& graph) {

    priority_queue<
        pii,
        vector<pii>,
        greater<pii>
    > pq;

    vector<bool> visited(V, false);

    int mstCost = 0;

    // {weight, node}
    pq.push({0, 0});

    while (!pq.empty()) {

        auto [weight, node] = pq.top();
        pq.pop();

        if (visited[node])
            continue;

        visited[node] = true;

        mstCost += weight;

        for (auto [neighbor, edgeWeight] : graph[node]) {

            if (!visited[neighbor]) {

                pq.push({
                    edgeWeight,
                    neighbor
                });
            }
        }
    }

    cout << "Minimum Cost = "
         << mstCost << endl;
}

int main() {

    int V = 5;

    vector<vector<pii>> graph(V);

    // Undirected weighted graph

    graph[0].push_back({1, 2});
    graph[1].push_back({0, 2});

    graph[0].push_back({3, 6});
    graph[3].push_back({0, 6});

    graph[1].push_back({2, 3});
    graph[2].push_back({1, 3});

    graph[1].push_back({3, 8});
    graph[3].push_back({1, 8});

    graph[1].push_back({4, 5});
    graph[4].push_back({1, 5});

    graph[2].push_back({4, 7});
    graph[4].push_back({2, 7});

    prims(V, graph);

    return 0;
}