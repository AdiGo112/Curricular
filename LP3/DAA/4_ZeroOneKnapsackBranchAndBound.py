import heapq


def bound(items, level, value, weight, capacity):
    for item_weight, item_value in items[level:]:
        take = min(item_weight, capacity - weight)
        value += item_value * take / item_weight
        weight += take
    return value


def knapsack(items, capacity):
    items = sorted(items, key=lambda item: item[1] / item[0], reverse=True)
    best = 0
    heap = [(-bound(items, 0, 0, 0, capacity), 0, 0, 0)]
    while heap:
        neg_bound, level, value, weight = heapq.heappop(heap)
        if -neg_bound <= best or level == len(items):
            continue
        item_weight, item_value = items[level]
        children = [(value, weight)]
        if weight + item_weight <= capacity:
            children.append((value + item_value, weight + item_weight))
        for child_value, child_weight in children:
            best = max(best, child_value)
            child_bound = bound(items, level + 1, child_value, child_weight, capacity)
            heapq.heappush(heap, (-child_bound, level + 1, child_value, child_weight))
    return best


n = int(input("Enter number of items: "))
items = [tuple(map(int, input(f"Weight and value of item {i + 1}: ").split())) for i in range(n)]
capacity = int(input("Enter knapsack capacity: "))
print("Maximum value =", knapsack(items, capacity))
