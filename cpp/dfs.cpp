#include <iostream>
#include <vector>

using namespace std;

void dfs(int node, vector<vector<int>> &graph, vector<bool> &visited) {

    visited[node] = true;

    cout << node << " ";

    for (int neighbor : graph[node]) {

        if (!visited[neighbor]) {

            dfs(neighbor, graph, visited);
        }
    }
}

int main() {

    int n = 5;

    vector<vector<int>> graph(n);

    graph[0] = {1, 2};
    graph[1] = {0, 3, 4};
    graph[2] = {0};
    graph[3] = {1};
    graph[4] = {1};

    vector<bool> visited(n, false);

    dfs(0, graph, visited);

    return 0;
}