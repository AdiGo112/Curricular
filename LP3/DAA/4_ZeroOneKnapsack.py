# =====================================================================
# Assignment 4: 0-1 Knapsack using Dynamic Programming
# =====================================================================
#
# Problem Statement:
#   Solve a 0-1 Knapsack problem using dynamic programming. Given item
#   weights and values and a knapsack capacity, maximize the total
#   value carried, where each item is either taken whole or not at all.
#
# Approach:
#   Build a table dp[i][capacity] = the best value achievable using
#   only the first i items with the given capacity. For each item,
#   either skip it (dp[i][c] = dp[i-1][c]) or take it, if it fits
#   (dp[i][c] = dp[i-1][c - weight] + value). Take whichever option is
#   larger. Because items cannot be split, unlike fractional knapsack,
#   a greedy ratio-based choice can be proven suboptimal here, so every
#   combination of "first i items, capacity c" must be considered via
#   this bottom-up table. The chosen items are then recovered by
#   backtracking through the table from dp[n][capacity] to dp[0][0].
#
# Complexity (n items, capacity C):
#   Time : O(n * C) -> one table cell computed per item/capacity pair.
#   Space: O(n * C) -> the dp table itself.
#
# Likely Viva Questions:
#   Q1. Why can't the fractional knapsack's greedy approach be used here?
#       A. Items must be taken whole or not at all, so always picking
#          the best ratio first can leave leftover capacity that cannot
#          be filled optimally — a counter-example is easy to construct.
#   Q2. What does dp[i][capacity] represent?
#       A. The maximum value obtainable using only the first i items
#          with a knapsack of size "capacity".
#   Q3. How are the selected items recovered after filling the table?
#       A. By backtracking from dp[n][capacity]: if dp[i][c] differs
#          from dp[i-1][c], item (i-1) was taken, so subtract its weight
#          from c and continue to row i-1; otherwise move to row i-1
#          at the same capacity.
# =====================================================================


# DP TABULATION
# Time complexity : O(numberOfItems * maxCapacity) -> one table cell per item/capacity pair
# Space complexity: O(numberOfItems * maxCapacity) -> the dp table itself

def zero_one_knapsack(items, max_capacity):

    # items: list of (weight, value)
    number_of_items = len(items)

    # dp[i][capacity] = best value achievable using the first i items
    # with a knapsack of the given capacity
    dp = [[0] * (max_capacity + 1) for _ in range(number_of_items + 1)]

    for i in range(1, number_of_items + 1):

        weight, value = items[i - 1]

        for capacity in range(max_capacity + 1):

            # Option 1: skip this item (always available)
            dp[i][capacity] = dp[i - 1][capacity]

            # Option 2: take this item, if it fits in the current capacity
            if weight <= capacity:
                value_if_taken = dp[i - 1][capacity - weight] + value
                if value_if_taken > dp[i][capacity]:
                    dp[i][capacity] = value_if_taken

    # Backtrack through the table to find which items were selected
    chosen_items = []
    remaining_capacity = max_capacity
    for i in range(number_of_items, 0, -1):

        # If the value changed between row i and row i-1 at this capacity,
        # item (i-1) must have been taken to reach it
        if dp[i][remaining_capacity] != dp[i - 1][remaining_capacity]:
            chosen_items.append(i - 1)
            remaining_capacity -= items[i - 1][0]

    return dp[number_of_items][max_capacity], chosen_items


# DRIVER CODE

# Sanity check against a hand-calculated result, kept separate from
# whatever the user enters at the input() prompts below.
# Classic sample: weights {1, 3, 4, 5}, values {1, 4, 5, 7}, capacity 7
# Expected maximum value: 9 (items with weight 3 and weight 4, value 4 + 5)
def run_self_test():
    sample_items = [(1, 1), (3, 4), (4, 5), (5, 7)]
    sample_max_value, _ = zero_one_knapsack(sample_items, 7)
    assert sample_max_value == 9


run_self_test()

# Ask the user for the number of items, each item's weight and value,
# and the knapsack's capacity.
number_of_items = int(input("Enter number of items: "))

items = []
for i in range(number_of_items):
    weight, value = map(int, input(f"Enter weight and value of item {i + 1} (space-separated): ").split())
    items.append((weight, value))

max_capacity = int(input("Enter knapsack capacity: "))

max_value, chosen_items = zero_one_knapsack(items, max_capacity)

print(f"\nMaximum value = {max_value}")
print("Items selected (weight, value):")
for item_index in chosen_items:
    print(f"  {items[item_index]}")
