# Assignment 3: Fractional Knapsack

## Problem statement
Write a program to solve a fractional Knapsack problem using a greedy method.

## Approach
Each item has a weight and a value, the knapsack has a capacity, and any
fraction of an item may be taken. The goal is the maximum total value.

1. Sort the items by value/weight ratio, highest first.
2. Go through them in that order and take as much of each as still fits:
   `take = min(weight, remaining capacity)`.
3. Add `value * take / weight` to the total and reduce the capacity.

Greedy is optimal here because items can be split: every unit of capacity is
filled with the most valuable weight still available, so nothing is wasted.

## Implementation notes
- Once the knapsack is full, `take` becomes 0 for every remaining item, so no
  separate "stop when full" check is needed.
- **C++** compares ratios by cross-multiplying (`a.value * b.weight >
  b.value * a.weight`) to avoid floating-point division in the sort.

## Example
Capacity 50, items (weight, value): (10, 60), (20, 100), (30, 120).
Ratios are 6, 5 and 4. Take all of the first two and 20/30 of the third:
`60 + 100 + 80 = 240`.

## Complexity
O(n log n) time for the sort, O(n) space.

## Viva prep

**Q: Why does greedy fail for 0-1 knapsack but work here?**
A: In 0-1 an item cannot be split, so taking the best ratio first can leave
capacity that no remaining item fits. Here the gap is filled with a fraction.

**Q: What is the greedy choice?**
A: Always take the item with the highest value per unit weight next.
