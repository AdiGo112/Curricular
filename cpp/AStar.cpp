#include <iostream>
#include <vector>
#include <queue>
#include <set>

using namespace std;

#define N 3

// Define the state of the puzzle
struct Node {
    Node* parent;
    vector<vector<int>> mat;
    int x, y;    // Coordinates of the blank tile (0)
    int cost;    // Heuristic cost: h(n)
    int level;   // Depth of the node: g(n)
};

// Function to print the N x N matrix
void printMatrix(const vector<vector<int>>& mat) {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            cout << mat[i][j] << " ";
        }
        cout << endl;
    }
}

// Function to allocate a new node
Node* newNode(vector<vector<int>> mat, int x, int y, int newX, int newY, int level, Node* parent) {
    Node* node = new Node;
    node->parent = parent;
    node->mat = mat;
    
    // Move the blank tile by swapping its position
    swap(node->mat[x][y], node->mat[newX][newY]);
    
    node->cost = INT_MAX;
    node->level = level;
    
    // Update the new blank tile coordinates
    node->x = newX;
    node->y = newY;
    
    return node;
}

// Function to calculate the number of misplaced tiles (Heuristic function h)
int calculateCost(const vector<vector<int>>& current, const vector<vector<int>>& target) {
    int count = 0;
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            if (current[i][j] && current[i][j] != target[i][j]) {
                count++;
            }
        }
    }
    return count;
}

// Function to check if a tile coordinate is within the matrix bounds
bool isSafe(int x, int y) {
    return (x >= 0 && x < N && y >= 0 && y < N);
}

// Function to print the path from the root node to the destination node
void printPath(Node* root) {
    if (root == nullptr) {
        return;
    }
    printPath(root->parent);
    printMatrix(root->mat);
    cout << "-----------" << endl;
}

// Custom comparator for the priority queue to order nodes by f(n) = g(n) + h(n)
struct comp {
    bool operator()(const Node* lhs, const Node* rhs) const {
        return (lhs->cost + lhs->level) > (rhs->cost + rhs->level);
    }
};

// A* algorithm function
void solve(vector<vector<int>> initial, int x, int y, vector<vector<int>> target) {
    // Priority queue to store live nodes of the search tree
    priority_queue<Node*, vector<Node*>, comp> pq;
    
    // Set to store visited states to avoid infinite loops and redundant calculations
    set<vector<vector<int>>> visited;

    // Create the root node and calculate its cost
    Node* root = newNode(initial, x, y, x, y, 0, nullptr);
    root->cost = calculateCost(initial, target);

    // Add root to the queue
    pq.push(root);

    // Arrays representing the 4 possible moves (bottom, left, top, right)
    int row[] = { 1, 0, -1, 0 };
    int col[] = { 0, -1, 0, 1 };

    while (!pq.empty()) {
        // Extract the node with the lowest estimated cost
        Node* min = pq.top();
        pq.pop();
        
        // Mark the current matrix state as visited
        visited.insert(min->mat);

        // If the estimated cost to reach the target is 0, we have found the goal
        if (min->cost == 0) {
            cout << "Solution Found! Steps taken: " << min->level << "\n\n";
            printPath(min);
            return;
        }

        // Generate all maximum 4 possible children for the current node
        for (int i = 0; i < 4; i++) {
            if (isSafe(min->x + row[i], min->y + col[i])) {
                // Create a child node
                Node* child = newNode(min->mat, min->x, min->y, min->x + row[i], min->y + col[i], min->level + 1, min);
                
                // If this state hasn't been visited yet, process it
                if (visited.find(child->mat) == visited.end()) {
                    child->cost = calculateCost(child->mat, target);
                    pq.push(child);
                } else {
                    // Free memory for nodes we don't need (avoid memory leaks)
                    delete child; 
                }
            }
        }
    }
    
    cout << "No solution exists for this configuration." << endl;
}

int main() {
    // 0 represents the blank space
    // Initial configuration
    vector<vector<int>> initial = {
        {1, 2, 0},
        {5, 3, 6},
        {7, 8, 4}
    };

    // Solved/Target configuration
    vector<vector<int>> target = {
        {1, 2, 3},
        {4, 5, 6},
        {7, 8, 0}
    };

    // Find the blank tile coordinates in the initial configuration
    int blank_x = 0, blank_y = 2; // Position of the blank tile (0)

    cout << "Solving 8-Puzzle using A* Algorithm..." << "\n\n";
    solve(initial, blank_x, blank_y, target);

    return 0;
}