# Assignment 3: Fractional Knapsack using a greedy method.
#
# Problem Statement:
#   Solve a fractional Knapsack problem using a greedy method.
#   Given item weights and values and a knapsack capacity, maximize the
#   total value carried, where any fraction of an item may be taken.
#
# Items can be split, so always taking the best value/weight ratio
# first never wastes capacity -- greedy is optimal here (unlike 0-1
# knapsack, where items can't be split).
#
# Time: O(n log n) for the sort by ratio. Space: O(n).


def fractional_knapsack(items, capacity):
    # items: list of (weight, value)
    order = sorted(range(len(items)), key=lambda i: items[i][1] / items[i][0], reverse=True)

    fractions = [0.0] * len(items)
    total_value = 0.0
    remaining = capacity

    for i in order:
        if remaining <= 0:
            break
        weight, value = items[i]
        if weight <= remaining:
            fractions[i] = 1.0
            total_value += value
            remaining -= weight
        else:
            frac = remaining / weight
            fractions[i] = frac
            total_value += value * frac
            remaining = 0

    return total_value, fractions


n = int(input("Enter number of items: "))
items = []
for i in range(n):
    weight, value = map(int, input(f"Enter weight and value of item {i + 1} (space-separated): ").split())
    items.append((weight, value))

capacity = int(input("Enter knapsack capacity: "))
max_value, fractions = fractional_knapsack(items, capacity)

print("\nItems (weight, value) and fraction taken:")
for (weight, value), fraction in zip(items, fractions):
    print(f"  ({weight}, {value}) -> fraction = {fraction}")
print(f"\nMaximum value = {max_value}")
