# Assignment 4: 0-1 Knapsack using dynamic programming.
#
# Problem Statement:
#   Solve a 0-1 Knapsack problem using dynamic programming. Given item
#   weights and values and a knapsack capacity, maximize the total
#   value carried, where each item is either taken whole or not at all.
#
# Items can't be split, so greedy by ratio can be suboptimal -- every
# (first i items, capacity c) combination is considered via a bottom-up
# table: dp[i][c] = best value using the first i items with capacity c.
#
# Time: O(n * capacity). Space: O(n * capacity).


def zero_one_knapsack(items, max_capacity):
    # items: list of (weight, value)
    n = len(items)
    dp = [[0] * (max_capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        weight, value = items[i - 1]
        for c in range(max_capacity + 1):
            dp[i][c] = dp[i - 1][c]  # skip item i-1
            if weight <= c:
                dp[i][c] = max(dp[i][c], dp[i - 1][c - weight] + value)

    # Backtrack: if the value changed from row i-1, item i-1 was taken.
    chosen = []
    c = max_capacity
    for i in range(n, 0, -1):
        if dp[i][c] != dp[i - 1][c]:
            chosen.append(i - 1)
            c -= items[i - 1][0]

    return dp[n][max_capacity], chosen


n = int(input("Enter number of items: "))
items = []
for i in range(n):
    weight, value = map(int, input(f"Enter weight and value of item {i + 1} (space-separated): ").split())
    items.append((weight, value))

capacity = int(input("Enter knapsack capacity: "))
max_value, chosen = zero_one_knapsack(items, capacity)

print(f"\nMaximum value = {max_value}")
print("Items selected (weight, value):")
for i in chosen:
    print(f"  {items[i]}")
