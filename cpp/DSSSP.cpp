#include <iostream>
#include <vector>
#include <queue>

using namespace std;

typedef pair<int, int> pii;

// Dijkstra Algorithm
void dijkstra(int source,
              vector<vector<pii>>& graph,
              int n) {

    vector<int> dist(n, 1e9);

    priority_queue<
        pii,
        vector<pii>,
        greater<pii>
    > pq;

    dist[source] = 0;

    pq.push({0, source});

    while (!pq.empty()) {

        auto [d, node] = pq.top();
        pq.pop();

        // Ignore outdated entries
        if (d > dist[node])
            continue;

        for (auto [neighbor, weight] : graph[node]) {

            if (dist[node] + weight < dist[neighbor]) {

                dist[neighbor] =
                    dist[node] + weight;

                pq.push({
                    dist[neighbor],
                    neighbor
                });
            }
        }
    }

    // Print shortest distances
    cout << "Shortest Distances:\n";

    for (int i = 0; i < n; i++) {

        cout << source
             << " -> "
             << i
             << " = "
             << dist[i]
             << endl;
    }
}

int main() {

    int n = 5;

    vector<vector<pii>> graph(n);

    // {neighbor, weight}

    graph[0].push_back({1, 4});
    graph[0].push_back({2, 1});

    graph[2].push_back({1, 2});
    graph[1].push_back({3, 1});

    graph[2].push_back({3, 5});
    graph[3].push_back({4, 3});

    dijkstra(1, graph, n);

    return 0;
}