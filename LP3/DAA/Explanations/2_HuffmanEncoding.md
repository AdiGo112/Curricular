# Assignment 2: Huffman Encoding

## Problem statement
Write a program to implement Huffman Encoding using a greedy strategy.

## Approach
Huffman coding gives frequent characters short codes and rare characters long
codes, so the encoded text is shorter than a fixed-length encoding.

1. Count the frequency of each character in the input text.
2. Put every character in a min-heap keyed by frequency.
3. Remove the two lowest-frequency nodes, join them under a new parent whose
   frequency is their sum, and push the parent back. Repeat until one node,
   the root, remains.
4. Walk the tree from the root: going left adds `0`, going right adds `1`.
   The path to each leaf is that character's code.

It is **greedy** because each step merges the two cheapest nodes and never
revisits that choice, yet the result is the optimal prefix code.

## Implementation notes
- **Prefix code**: characters sit only at leaves, so no code is a prefix of
  another and the bitstring decodes without separators.
- **Single distinct character**: the tree is one leaf with an empty path, so
  it is given the code `0`.
- **Python**: heap entries are `(frequency, id, node)`. The unique `id` breaks
  frequency ties so the heap never has to compare two nodes. A leaf is the
  character itself, an internal node is a `(left, right)` tuple.
- **C++**: `priority_queue` is a max-heap by default, so the comparator is
  reversed to keep the smallest frequency on top.

## Example
Input `aabbbcc` has frequencies a=2, b=3, c=2.

| Character | Code |
| --- | --- |
| b | 0 |
| a | 10 |
| c | 11 |

The text takes 11 bits instead of 56 bits at 8 bits per character.

## Complexity
For `k` distinct characters: O(k log k) time to build the tree, O(k) space.

## Viva prep

**Q: Why a min-heap?**
A: Each step needs the two smallest frequencies. A heap gives them in
O(log k) instead of scanning the whole list.

**Q: Is the Huffman code unique?**
A: No. Ties and the left/right choice can change the codes, but every valid
Huffman tree gives the same total encoded length.

**Q: When does Huffman coding give no benefit?**
A: When all characters are equally frequent, the codes come out the same
length as a fixed-length encoding.
