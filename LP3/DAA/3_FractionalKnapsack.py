def fractional_knapsack(items, capacity):
    total = 0
    for weight, value in sorted(items, key=lambda item: item[1] / item[0], reverse=True):
        take = min(weight, capacity)
        total += value * take / weight
        capacity -= take
    return total


n = int(input("Enter number of items: "))
items = [tuple(map(int, input(f"Weight and value of item {i + 1}: ").split())) for i in range(n)]
capacity = int(input("Enter knapsack capacity: "))
print("Maximum value =", fractional_knapsack(items, capacity))
