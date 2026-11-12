# Assignment 2: Huffman Encoding using a greedy strategy.
#
# Problem Statement:
#   Implement Huffman Encoding using a greedy strategy.
#
# Build a min-heap of characters keyed by frequency, repeatedly merge
# the two lowest-frequency nodes until one tree remains, then walk the
# tree (0=left, 1=right) to assign each character a prefix code.
# Greedy because the merge order is never revisited, yet it still
# yields the minimum expected code length.
#
# Time: O(k log k) to build the tree for k distinct chars, + O(m) to
# encode an m-length string. Space: O(k).

import heapq
from collections import Counter


class Node:
    def __init__(self, ch, freq, left=None, right=None):
        self.ch = ch
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other):  # lets heapq compare nodes by frequency only
        return self.freq < other.freq


def build_huffman_tree(freq):
    min_heap = [Node(ch, f) for ch, f in freq.items()]
    heapq.heapify(min_heap)

    # Single-character edge case: give it a dummy sibling so it gets a code.
    if len(min_heap) == 1:
        only = heapq.heappop(min_heap)
        heapq.heappush(min_heap, Node('\0', 0, only, None))

    while len(min_heap) > 1:
        left = heapq.heappop(min_heap)
        right = heapq.heappop(min_heap)
        heapq.heappush(min_heap, Node('\0', left.freq + right.freq, left, right))

    return min_heap[0]


def generate_codes(root, code, codes):
    if root is None:
        return
    if root.left is None and root.right is None:
        codes[root.ch] = code if code else "0"
        return
    generate_codes(root.left, code + "0", codes)
    generate_codes(root.right, code + "1", codes)


text = input("Enter the string to encode: ")
if not text:
    print("Empty string entered, nothing to encode.")
    raise SystemExit

freq = Counter(text)
root = build_huffman_tree(freq)
codes = {}
generate_codes(root, "", codes)

print("Character frequencies and Huffman codes:")
for ch, f in freq.items():
    print(f"  '{ch}' : freq = {f}, code = {codes[ch]}")

encoded = "".join(codes[c] for c in text)
print(f"\nEncoded bitstring: {encoded}")
print(f"Fixed-length (8-bit) size: {len(text) * 8} bits")
print(f"Huffman-encoded size     : {len(encoded)} bits")
