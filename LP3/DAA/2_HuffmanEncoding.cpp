// Assignment 2: Huffman Encoding using a greedy strategy.
//
// Problem Statement:
//   Implement Huffman Encoding using a greedy strategy.
//
// Build a min-heap of characters keyed by frequency, repeatedly merge
// the two lowest-frequency nodes until one tree remains, then walk the
// tree (0=left, 1=right) to assign each character a prefix code.
// Greedy because the merge order is never revisited, yet it still
// yields the minimum expected code length.
//
// Time: O(k log k) to build the tree for k distinct chars, + O(m) to
// encode an m-length string. Space: O(k).

#include <iostream>
#include <vector>
#include <queue>
#include <unordered_map>
using namespace std;

struct Node {
    char ch;
    int freq;
    Node *left, *right;
    Node(char ch, int freq, Node *left = nullptr, Node *right = nullptr)
        : ch(ch), freq(freq), left(left), right(right) {}
};

// Min-heap comparator: smallest frequency on top.
struct Compare {
    bool operator()(Node *a, Node *b) { return a->freq > b->freq; }
};

Node *buildHuffmanTree(unordered_map<char, int> &freq) {
    priority_queue<Node *, vector<Node *>, Compare> minHeap;
    for (auto &p : freq)
        minHeap.push(new Node(p.first, p.second));

    // Single-character edge case: give it a dummy sibling so it gets a code.
    if (minHeap.size() == 1) {
        Node *only = minHeap.top();
        minHeap.pop();
        minHeap.push(new Node('\0', 0, only, nullptr));
    }

    while (minHeap.size() > 1) {
        Node *left = minHeap.top(); minHeap.pop();
        Node *right = minHeap.top(); minHeap.pop();
        minHeap.push(new Node('\0', left->freq + right->freq, left, right));
    }
    return minHeap.top();
}

void generateCodes(Node *root, string code, unordered_map<char, string> &codes) {
    if (!root) return;
    if (!root->left && !root->right) {
        codes[root->ch] = code.empty() ? "0" : code;
        return;
    }
    generateCodes(root->left, code + "0", codes);
    generateCodes(root->right, code + "1", codes);
}

int main() {
    string text;
    cout << "Enter the string to encode: ";
    getline(cin, text);
    if (text.empty()) {
        cout << "Empty string entered, nothing to encode.\n";
        return 0;
    }

    unordered_map<char, int> freq;
    for (char c : text) freq[c]++;

    Node *root = buildHuffmanTree(freq);
    unordered_map<char, string> codes;
    generateCodes(root, "", codes);

    cout << "Character frequencies and Huffman codes:\n";
    for (auto &p : freq)
        cout << "  '" << p.first << "' : freq = " << p.second << ", code = " << codes[p.first] << "\n";

    string encoded;
    for (char c : text) encoded += codes[c];

    cout << "\nEncoded bitstring: " << encoded << "\n";
    cout << "Fixed-length (8-bit) size: " << text.size() * 8 << " bits\n";
    cout << "Huffman-encoded size     : " << encoded.size() << " bits\n";
    return 0;
}
