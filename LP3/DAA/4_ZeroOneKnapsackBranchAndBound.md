# Assignment 4: 0-1 Knapsack using Branch and Bound

## Problem statement
Write a program to solve a 0-1 Knapsack problem using dynamic programming or
branch and bound strategy. This file covers branch and bound; dynamic
programming is in `4_ZeroOneKnapsackDP.md`.

## Approach
The search space is a binary tree: at level `i` the item `i` is either taken
or skipped. Exploring all of it is 2^n nodes. Branch and bound skips whole
subtrees that cannot beat the best answer found so far.

1. Sort items by value/weight ratio, highest first.
2. Each node stores `level` (the next item to decide), the `value` and
   `weight` collected so far, and a `bound`.
3. **Bound** = an upper limit on what this node can still reach: its value
   plus the remaining items filled in greedily, the last one fractionally.
   This is the fractional knapsack answer for what is left, and the real 0-1
   answer can never exceed it.
4. Nodes wait in a max-heap ordered by bound, so the most promising node is
   expanded first (best-first search).
5. Expanding a node creates two children: take the item (only if it fits) and
   skip the item. `best` is updated whenever a taken child improves it.
6. **Prune**: a node whose bound is not above `best` is dropped.

## Implementation notes
- Sorting by ratio makes the bound tight, which prunes earlier.
- **Python**: `heapq` is a min-heap, so the bound is stored negated.
- **C++**: `Node` defines `operator<` on the bound, which is what
  `priority_queue` needs to act as a max-heap.

## Example
Capacity 5, items (weight, value): (2, 3), (3, 4), (4, 5), (5, 6).
The answer is 7, the same as dynamic programming, after expanding only a few
nodes instead of all 16 combinations.

## Complexity
O(2^n) time and space in the worst case. In practice far fewer nodes are
visited because of pruning.

## Dynamic programming vs branch and bound

| | Dynamic programming | Branch and bound |
| --- | --- | --- |
| Time | O(n * capacity) | O(2^n) worst case |
| Depends on capacity | Yes | No |
| Works with fractional weights | No | Yes |

## Viva prep

**Q: What is the bounding function here?**
A: The fractional knapsack value of the remaining items added to the node's
current value.

**Q: Why best-first rather than depth-first?**
A: Expanding the highest bound first finds a good `best` early, and a higher
`best` prunes more nodes.

**Q: How is this different from backtracking?**
A: Backtracking prunes only on feasibility (does it still fit). Branch and
bound also prunes on optimality (can it still beat the best answer).
