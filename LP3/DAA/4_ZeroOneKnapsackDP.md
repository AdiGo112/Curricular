# Assignment 4: 0-1 Knapsack using Dynamic Programming

## Problem statement
Write a program to solve a 0-1 Knapsack problem using dynamic programming or
branch and bound strategy. This file covers dynamic programming; branch and
bound is in `4_ZeroOneKnapsackBranchAndBound.md`.

## Approach
Each item is either taken whole or left out. Greedy by ratio can be wrong
here, so every combination has to be considered, without recomputing shared
subproblems.

`dp[c]` = the best value achievable with capacity `c` using the items seen so
far. For each item, every capacity that can hold it is updated:

```
dp[c] = max(dp[c], dp[c - weight] + value)
```

The first option skips the item, the second takes it. The answer is
`dp[capacity]`.

## Implementation notes
- The textbook table is 2D, `dp[i][c]` for the first `i` items. Row `i` only
  reads row `i-1`, so one row is enough.
- The capacity loop runs **downwards**. Going upwards would let `dp[c - weight]`
  already include the current item, which would allow taking it twice (that is
  the unbounded knapsack).

## Example
Capacity 5, items (weight, value): (2, 3), (3, 4), (4, 5), (5, 6).
The best choice is the first two items: weight 5, value 7.

## Complexity
O(n * capacity) time, O(capacity) space.

## Viva prep

**Q: Why is this dynamic programming?**
A: The problem has overlapping subproblems (the same remaining capacity is
reached by different choices) and optimal substructure (the best answer is
built from best answers to smaller capacities).

**Q: Is O(n * capacity) polynomial?**
A: It is pseudo-polynomial. It depends on the numeric value of the capacity,
not on the number of bits needed to write it.

**Q: How would you find which items were chosen?**
A: Keep the full 2D table and walk back from `dp[n][capacity]`: if the value
differs from the row above, that item was taken.
