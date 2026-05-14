from collections import deque

# Undirected Graph using Adjacency List
graph = {
    'A': ['B', 'C', 'G', 'H'],
    'B': ['A', 'D', 'E'],
    'C': ['A', 'F'],
    'D': ['B', 'F'],
    'E': ['B', 'G'],
    'F': ['C', 'D'],
    'G': ['A', 'E'],
    'H': ['A']
}


# ---------------- DFS ----------------
def dfs(graph, start, visited=None, traversal=None):

    if visited is None:
        visited = set()

    if traversal is None:
        traversal = []

    # Mark node as visited
    visited.add(start)

    # Store traversal
    traversal.append(start)

    # Visit neighbors recursively
    for neighbor in graph[start]:
        if neighbor not in visited:
            dfs(graph, neighbor, visited, traversal)

    return traversal


# ---------------- BFS ----------------
def bfs(graph, start):

    visited = set()
    traversal = []

    # Queue for BFS
    queue = deque([start])

    # Mark start node as visited
    visited.add(start)

    while queue:

        # Remove front element
        vertex = queue.popleft()

        # Store traversal
        traversal.append(vertex)

        # Visit neighbors
        for neighbor in graph[vertex]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return traversal


# ---------------- Driver Code ----------------
print("DFS Traversal:")
print(dfs(graph, 'A'))

print("\nBFS Traversal:")
print(bfs(graph, 'A'))