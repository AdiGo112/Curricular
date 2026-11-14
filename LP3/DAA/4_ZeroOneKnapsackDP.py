def knapsack(items, capacity):
    dp = [0] * (capacity + 1)
    for weight, value in items:
        for c in range(capacity, weight - 1, -1):
            dp[c] = max(dp[c], dp[c - weight] + value)
    return dp[capacity]


n = int(input("Enter number of items: "))
items = [tuple(map(int, input(f"Weight and value of item {i + 1}: ").split())) for i in range(n)]
capacity = int(input("Enter knapsack capacity: "))
print("Maximum value =", knapsack(items, capacity))
