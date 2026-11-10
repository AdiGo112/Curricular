# =====================================================================
# Assignment 2: Huffman Encoding using a Greedy Strategy
# =====================================================================
#
# Problem Statement:
#   Implement Huffman Encoding using a greedy strategy.
#
# Approach:
#   1. Count the frequency of every character in the input string.
#   2. Put every character in a min-heap keyed by frequency.
#   3. Repeatedly pop the two lowest-frequency nodes and merge them
#      into a new internal node (frequency = sum of the two), pushing
#      it back into the heap, until only one node (the tree root)
#      remains. This greedy merge of the two cheapest nodes at every
#      step is what produces a minimum expected code length overall.
#   4. Walk the tree (0 = left, 1 = right) to assign a prefix code to
#      each character; frequent characters end up closer to the root
#      and so get shorter codes.
#
# Complexity (for k distinct characters, input length m):
#   Time : O(k log k) to build the tree (k-1 heap merges, each O(log k))
#          + O(m) to encode the string once codes are known.
#   Space: O(k) for the heap and the tree nodes.
#
# Likely Viva Questions:
#   Q1. Why is Huffman coding called greedy?
#       A. At each step it merges the two currently lowest-frequency
#          nodes without ever reconsidering that choice later, and this
#          sequence of locally optimal merges yields a globally optimal
#          (minimum expected length) prefix code.
#   Q2. Why must the code be a prefix code?
#       A. So the encoded bitstream can be decoded unambiguously by
#          walking the tree bit by bit, with no separators needed.
#   Q3. What happens with only one distinct character?
#       A. It would get an empty code if left alone, so the code gives
#          it a dummy sibling node to force a valid non-empty code.
# =====================================================================

import heapq
from collections import Counter


# TREE NODE

class Node:

    def __init__(self, ch, freq, left=None, right=None):
        self.ch = ch
        self.freq = freq
        self.left = left
        self.right = right

    # Needed so heapq can break freq ties without comparing Node objects
    def __lt__(self, other):
        return self.freq < other.freq


# BUILD HUFFMAN TREE (GREEDY STEP)
# Repeatedly pick the two least-frequent nodes and merge them.
# Time complexity : O(k log k) for k distinct characters
# Space complexity: O(k) for the heap and the tree

def build_huffman_tree(freq):

    min_heap = [Node(ch, f) for ch, f in freq.items()]
    heapq.heapify(min_heap)

    # Single character edge case: give it a dummy sibling so it gets a code
    if len(min_heap) == 1:
        only = heapq.heappop(min_heap)
        heapq.heappush(min_heap, Node('\0', 0, only, None))

    while len(min_heap) > 1:
        left = heapq.heappop(min_heap)
        right = heapq.heappop(min_heap)
        merged = Node('\0', left.freq + right.freq, left, right)
        heapq.heappush(min_heap, merged)

    return min_heap[0]


# Walk the tree and collect the prefix code for each character
def generate_codes(root, code, codes):

    if root is None:
        return

    # Leaf node
    if root.left is None and root.right is None:
        codes[root.ch] = code if code else "0"
        return

    generate_codes(root.left, code + "0", codes)
    generate_codes(root.right, code + "1", codes)


# DRIVER CODE

def count_frequencies(text):
    return Counter(text)


def encode_text(text, codes):
    return "".join(codes[c] for c in text)


# Sanity check against a hand-computable fact, kept separate from
# whatever the user enters at the input() prompt below: a Huffman code
# is never longer than fixed-length 8-bit encoding.
def run_self_test():
    sample_text = "huffman greedy encoding"
    sample_freq = count_frequencies(sample_text)
    sample_root = build_huffman_tree(sample_freq)
    sample_codes = {}
    generate_codes(sample_root, "", sample_codes)
    sample_encoded = encode_text(sample_text, sample_codes)
    assert len(sample_encoded) <= len(sample_text) * 8


def print_frequencies_and_codes(freq, codes):
    print("Character frequencies and Huffman codes:")
    for ch, f in freq.items():
        print(f"  '{ch}' : freq = {f}, code = {codes[ch]}")


# Print the encoded string and its compression ratio vs fixed-length (8-bit) encoding
def print_encoding_summary(text, encoded):
    fixed_bits = len(text) * 8
    huffman_bits = len(encoded)
    ratio = huffman_bits / fixed_bits

    print(f"\nOriginal string : {text}")
    print(f"Encoded bitstring: {encoded}")
    print(f"\nFixed-length (8-bit) size : {fixed_bits} bits")
    print(f"Huffman-encoded size      : {huffman_bits} bits")
    print(f"Compression ratio         : {ratio:.4f} (lower is better)")


run_self_test()

# Ask the user for the string to encode.
text = input("Enter the string to encode: ")

if not text:
    print("Empty string entered, nothing to encode.")
    raise SystemExit

freq = count_frequencies(text)
root = build_huffman_tree(freq)

codes = {}
generate_codes(root, "", codes)

print_frequencies_and_codes(freq, codes)

encoded = encode_text(text, codes)
print_encoding_summary(text, encoded)

# Sanity check: Huffman encoding must never be larger than fixed-length
assert len(encoded) <= len(text) * 8
