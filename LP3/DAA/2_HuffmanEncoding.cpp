// =====================================================================
// Assignment 2: Huffman Encoding using a Greedy Strategy
// =====================================================================
//
// Problem Statement:
//   Implement Huffman Encoding using a greedy strategy.
//
// Approach:
//   1. Count the frequency of every character in the input string.
//   2. Put every character in a min-heap keyed by frequency.
//   3. Repeatedly pop the two lowest-frequency nodes and merge them
//      into a new internal node (frequency = sum of the two), pushing
//      it back into the heap, until only one node (the tree root)
//      remains. This greedy merge of the two cheapest nodes at every
//      step is what produces a minimum expected code length overall.
//   4. Walk the tree (0 = left, 1 = right) to assign a prefix code to
//      each character; frequent characters end up closer to the root
//      and so get shorter codes.
//
// Complexity (for k distinct characters, input length m):
//   Time : O(k log k) to build the tree (k-1 heap merges, each O(log k))
//          + O(m) to encode the string once codes are known.
//   Space: O(k) for the heap and the tree nodes.
//
// Likely Viva Questions:
//   Q1. Why is Huffman coding called greedy?
//       A. At each step it merges the two currently lowest-frequency
//          nodes without ever reconsidering that choice later, and this
//          sequence of locally optimal merges yields a globally optimal
//          (minimum expected length) prefix code.
//   Q2. Why must the code be a prefix code?
//       A. So the encoded bitstream can be decoded unambiguously by
//          walking the tree bit by bit, with no separators needed.
//   Q3. What happens with only one distinct character?
//       A. It would get an empty code if left alone, so the code gives
//          it a dummy sibling node to force a valid non-empty code.
// =====================================================================

#include <iostream>
#include <vector>
#include <queue>
#include <unordered_map>
#include <cassert>

using namespace std;

// TREE NODE

struct Node {

    char ch;
    int freq;
    Node *left, *right;

    Node(char ch, int freq, Node *left = nullptr, Node *right = nullptr)
        : ch(ch), freq(freq), left(left), right(right) {}
};

// Comparator for the min-heap (smallest frequency on top)
struct Compare {

    bool operator()(Node *a, Node *b) {
        return a->freq > b->freq;
    }
};

// BUILD HUFFMAN TREE (GREEDY STEP)
// Repeatedly pick the two least-frequent nodes and merge them.
// Time complexity : O(k log k) for k distinct characters
// Space complexity: O(k) for the heap and the tree

Node *buildHuffmanTree(unordered_map<char, int> &freq) {

    priority_queue<Node *, vector<Node *>, Compare> minHeap;

    for (auto &p : freq)
        minHeap.push(new Node(p.first, p.second));

    // Single character edge case: give it a dummy sibling so it gets a code
    if (minHeap.size() == 1) {

        Node *only = minHeap.top();
        minHeap.pop();
        minHeap.push(new Node('\0', 0, only, nullptr));
    }

    while (minHeap.size() > 1) {

        Node *left = minHeap.top(); minHeap.pop();
        Node *right = minHeap.top(); minHeap.pop();

        Node *merged = new Node('\0', left->freq + right->freq, left, right);
        minHeap.push(merged);
    }

    return minHeap.top();
}

// Walk the tree and collect the prefix code for each character
void generateCodes(Node *root, string code, unordered_map<char, string> &codes) {

    if (!root)
        return;

    // Leaf node
    if (!root->left && !root->right) {
        codes[root->ch] = code.empty() ? "0" : code;
        return;
    }

    generateCodes(root->left, code + "0", codes);
    generateCodes(root->right, code + "1", codes);
}

void freeTree(Node *root) {

    if (!root)
        return;

    freeTree(root->left);
    freeTree(root->right);
    delete root;
}

// Count how many times each character occurs in the text
unordered_map<char, int> countFrequencies(const string &text) {

    unordered_map<char, int> freq;
    for (char c : text)
        freq[c]++;

    return freq;
}

// Encode a string using already-generated prefix codes
string encodeText(const string &text, unordered_map<char, string> &codes) {

    string encoded;
    for (char c : text)
        encoded += codes[c];

    return encoded;
}

// Sanity check against a hand-computable fact, kept separate from
// whatever the user enters at the prompt in main(): a Huffman code is
// never longer than fixed-length 8-bit encoding.
void runSelfTest() {

    string sampleText = "huffman greedy encoding";
    unordered_map<char, int> sampleFreq = countFrequencies(sampleText);

    Node *sampleRoot = buildHuffmanTree(sampleFreq);
    unordered_map<char, string> sampleCodes;
    generateCodes(sampleRoot, "", sampleCodes);

    string sampleEncoded = encodeText(sampleText, sampleCodes);
    assert((int)sampleEncoded.size() <= (int)sampleText.size() * 8);

    freeTree(sampleRoot);
}

void printFrequenciesAndCodes(unordered_map<char, int> &freq, unordered_map<char, string> &codes) {

    cout << "Character frequencies and Huffman codes:\n";
    for (auto &p : freq)
        cout << "  '" << p.first << "' : freq = " << p.second
             << ", code = " << codes[p.first] << "\n";
}

// Print the encoded string and its compression ratio vs fixed-length (8-bit) encoding
void printEncodingSummary(const string &text, const string &encoded) {

    int fixedBits = text.size() * 8;
    int huffmanBits = encoded.size();
    double ratio = (double)huffmanBits / fixedBits;

    cout << "\nOriginal string : " << text << "\n";
    cout << "Encoded bitstring: " << encoded << "\n";
    cout << "\nFixed-length (8-bit) size : " << fixedBits << " bits\n";
    cout << "Huffman-encoded size      : " << huffmanBits << " bits\n";
    cout << "Compression ratio         : " << ratio << " (lower is better)\n";
}

int main() {

    runSelfTest();

    // DRIVER CODE
    // Ask the user for the string to encode.
    string text;
    cout << "Enter the string to encode: ";
    getline(cin, text);

    if (text.empty()) {
        cout << "Empty string entered, nothing to encode.\n";
        return 0;
    }

    unordered_map<char, int> freq = countFrequencies(text);
    Node *root = buildHuffmanTree(freq);

    unordered_map<char, string> codes;
    generateCodes(root, "", codes);

    printFrequenciesAndCodes(freq, codes);

    string encoded = encodeText(text, codes);
    printEncodingSummary(text, encoded);

    freeTree(root);
    return 0;
}
