#include <iostream>
#include <map>
#include <queue>
#include <vector>
using namespace std;

struct Node {
    char ch;
    int freq;
    Node *left, *right;
};

struct Compare {
    bool operator()(Node *a, Node *b) { return a->freq > b->freq; }
};

Node *buildTree(const string &text) {
    map<char, int> freq;
    for (char c : text) freq[c]++;

    priority_queue<Node *, vector<Node *>, Compare> pq;
    for (auto &p : freq) pq.push(new Node{p.first, p.second, nullptr, nullptr});

    while (pq.size() > 1) {
        Node *left = pq.top(); pq.pop();
        Node *right = pq.top(); pq.pop();
        pq.push(new Node{'\0', left->freq + right->freq, left, right});
    }
    return pq.top();
}

void printCodes(Node *node, string code) {
    if (!node->left) {
        cout << node->ch << " : " << (code.empty() ? "0" : code) << "\n";
        return;
    }
    printCodes(node->left, code + "0");
    printCodes(node->right, code + "1");
}

int main() {
    string text;
    cout << "Enter text: ";
    getline(cin, text);
    if (!text.empty()) printCodes(buildTree(text), "");
}
