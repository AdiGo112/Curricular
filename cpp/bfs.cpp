#include <iostream>
#include <vector>
#include <queue>

using namespace std;

void bfs(int start, vector<vector<int>> &graph, int n)
{

    vector<bool> visited(n, false);

    queue<int> q;

    visited[start] = true;
    q.push(start);

    while (!q.empty())
    {

        int node = q.front();
        q.pop();

        cout << node << " ";

        for (int neighbor : graph[node])
        {

            if (!visited[neighbor])
            {

                visited[neighbor] = true;
                q.push(neighbor);
            }
        }
    }
}

int main()
{

    int n = 5;

    vector<vector<int>> graph(n);

    graph[0] = {1, 2};
    graph[1] = {0, 3, 4};
    graph[2] = {0};
    graph[3] = {1};
    graph[4] = {1};

    bfs(0, graph, n);

    return 0;
}