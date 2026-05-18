#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

struct Edge {
    int u, v, w;
};

// DSU (Disjoint Set Union)
class DSU {

    vector<int> parent;

public:

    DSU(int n) {

        parent.resize(n);

        for (int i = 0; i < n; i++)
            parent[i] = i;
    }

    int find(int x) {

        if (parent[x] == x)
            return x;

        return parent[x] = find(parent[x]);
    }

    bool unite(int a, int b) {

        a = find(a);
        b = find(b);

        if (a == b)
            return false;

        parent[a] = b;

        return true;
    }
};

bool compare(Edge a, Edge b) {
    return a.w < b.w;
}

void kruskal(int V, vector<Edge>& edges) {

    sort(edges.begin(), edges.end(), compare);

    DSU dsu(V);

    int mstCost = 0;

    for (auto edge : edges) {

        if (dsu.unite(edge.u, edge.v)) {

            mstCost += edge.w;
        }
    }

    cout << "Minimum Cost = "
         << mstCost << endl;
}

int main() {

    int V = 5;

    vector<Edge> edges = {

        {0, 1, 2},
        {0, 3, 6},
        {1, 2, 3},
        {1, 3, 8},
        {1, 4, 5},
        {2, 4, 7}
    };

    kruskal(V, edges);

    return 0;
}