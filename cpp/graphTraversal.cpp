#include <iostream>
#include <vector>
#include <queue>

using namespace std;

class Graph {

    int V;
    vector<vector<int>> adj;

public:

    Graph(int vertices) {
        V = vertices;
        adj.resize(V);
    }

    // Add undirected edge
    void addEdge(int u, int v) {

        adj[u].push_back(v);
        adj[v].push_back(u);
    }

    // DFS Helper
    void dfsUtil(int node, vector<bool>& visited) {

        visited[node] = true;

        cout << node << " ";

        for (int neighbor : adj[node]) {

            if (!visited[neighbor]) {
                dfsUtil(neighbor, visited);
            }
        }
    }

    // DFS Traversal
    void DFS(int start) {

        vector<bool> visited(V, false);

        cout << "\nDFS Traversal: ";
        dfsUtil(start, visited);

        cout << endl;
    }

    // BFS Traversal
    void BFS(int start) {

        vector<bool> visited(V, false);

        queue<int> q;

        visited[start] = true;
        q.push(start);

        cout << "\nBFS Traversal: ";

        while (!q.empty()) {

            int node = q.front();
            q.pop();

            cout << node << " ";

            for (int neighbor : adj[node]) {

                if (!visited[neighbor]) {

                    visited[neighbor] = true;
                    q.push(neighbor);
                }
            }
        }

        cout << endl;
    }
};

int main() {

    int V = 5;

    Graph g(V);

    // Sample Graph
    g.addEdge(0, 1);
    g.addEdge(0, 2);
    g.addEdge(1, 3);
    g.addEdge(1, 4);

    int choice, start;

    while (true) {

        cout << "\n--- MENU ---\n";
        cout << "1. DFS\n";
        cout << "2. BFS\n";
        cout << "3. Exit\n";

        cout << "Enter Choice: ";
        cin >> choice;

        if (choice == 3)
            break;
        switch (choice) {

            case 1:
                cout << "Enter Starting Node: ";
                cin >> start;
                g.DFS(start);
                break;

            case 2:
                cout << "Enter Starting Node: ";
                cin >> start;
                g.BFS(start);
                break;

            default:
                cout << "Invalid Choice\n";
        }
    }

    return 0;
}