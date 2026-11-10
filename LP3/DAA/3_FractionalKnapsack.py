# =====================================================================
# Assignment 3: Fractional Knapsack using a Greedy Method
# =====================================================================
#
# Problem Statement:
#   Solve a fractional Knapsack problem using a greedy method.
#   Given item weights and values and a knapsack capacity, maximize the
#   total value carried, where any fraction of an item may be taken.
#
# Approach:
#   1. Compute each item's value/weight ratio.
#   2. Sort items by this ratio, descending.
#   3. Take items whole, highest ratio first, while they fit.
#   4. When the next item no longer fits whole, take just enough of it
#      (a fraction) to exactly fill the remaining capacity, then stop.
#   This greedy rule is optimal here because items are divisible: there
#   is never a reason to leave capacity unused when a higher-ratio item
#   could still fill it, even partially.
#
# Complexity (n items):
#   Time : O(n log n) -> dominated by sorting items by ratio.
#   Space: O(n)        -> storage for the order and fraction taken.
#
# Likely Viva Questions:
#   Q1. Why does greedy work for fractional knapsack but not 0-1 knapsack?
#       A. Because items can be split, filling the capacity with the
#          best ratio first never wastes capacity; any leftover space
#          can always be filled with a fraction of the next best item.
#          0-1 knapsack cannot split items, so this guarantee fails.
#   Q2. What is the greedy criterion used?
#       A. The value-to-weight ratio (value / weight) of each item.
#   Q3. When does a fractional (non-whole) amount get taken?
#       A. At most once per run: for the first item (in ratio order)
#          that does not fully fit in the remaining capacity.
# =====================================================================


# GREEDY FRACTIONAL KNAPSACK
# Time complexity : O(n log n) -> dominated by the sort on ratio
# Space complexity: O(n)       -> storage for the fractions

def fractional_knapsack(items, capacity):

    # items: list of (weight, value)
    number_of_items = len(items)

    # Sort the item indices by value/weight ratio, descending
    order = sorted(
        range(number_of_items),
        key=lambda index: items[index][1] / items[index][0],
        reverse=True
    )

    fractions = [0.0] * number_of_items
    total_value = 0.0
    remaining_capacity = capacity

    for item_index in order:

        if remaining_capacity <= 0:
            break

        weight, value = items[item_index]

        if weight <= remaining_capacity:

            # Take the whole item
            fractions[item_index] = 1.0
            total_value += value
            remaining_capacity -= weight

        else:

            # Take only a fraction of the item to fill the remaining capacity
            fraction_taken = remaining_capacity / weight
            fractions[item_index] = fraction_taken
            total_value += value * fraction_taken
            remaining_capacity = 0

    return total_value, fractions


# DRIVER CODE

# Sanity check against a hand-calculated result, kept separate from
# whatever the user enters at the input() prompts below.
# Classic sample: weights {10, 20, 30}, values {60, 100, 120}, capacity 50
# Expected maximum value: 240.0
def run_self_test():
    sample_items = [(10, 60), (20, 100), (30, 120)]
    sample_max_value, _ = fractional_knapsack(sample_items, 50)
    assert abs(sample_max_value - 240.0) < 1e-9


run_self_test()

# Ask the user for the number of items, each item's weight and value,
# and the knapsack's capacity.
number_of_items = int(input("Enter number of items: "))

items = []
for i in range(number_of_items):
    weight, value = map(int, input(f"Enter weight and value of item {i + 1} (space-separated): ").split())
    items.append((weight, value))

capacity = int(input("Enter knapsack capacity: "))

max_value, fractions = fractional_knapsack(items, capacity)

print("\nItems (weight, value) and fraction taken:")
for (weight, value), fraction in zip(items, fractions):
    print(f"  ({weight}, {value}) -> fraction = {fraction}")

print(f"\nMaximum value = {max_value}")
