import heapq

# MINIMUM SPANNING TREE USING PRIM'S ALGORITHM


# =========================================================
# ADJACENCY LIST REPRESENTATION
# =========================================================

# Graph represented using adjacency list
# Format:
# Vertex : [(Neighbor, Weight)]

graph_list = {
    'A': [('B', 2), ('C', 3)],
    'B': [('A', 2), ('C', 1), ('D', 4)],
    'C': [('A', 3), ('B', 1), ('D', 5)],
    'D': [('B', 4), ('C', 5)]
}


# Prim's Algorithm using Adjacency List
def prim_list(graph, start):

    # Store visited vertices
    visited = set()

    # Min Heap / Priority Queue
    # Stores (weight, vertex)
    min_heap = [(0, start)]

    # Store total cost of MST
    total_cost = 0

    print("MST using Adjacency List:\n")

    # Continue until heap becomes empty
    while min_heap:

        # Remove minimum weight edge
        weight, vertex = heapq.heappop(min_heap)

        # Skip already visited vertices
        if vertex in visited:
            continue

        # Mark current vertex as visited
        visited.add(vertex)

        # Add edge weight to total cost
        total_cost += weight

        # Print selected vertex and weight
        print(vertex, "-", weight)

        # Traverse neighboring vertices
        for neighbor, edge_weight in graph[vertex]:

            # Add unvisited neighbors to heap
            if neighbor not in visited:

                heapq.heappush(
                    min_heap,
                    (edge_weight, neighbor)
                )

    # Print total cost of MST
    print("\nTotal Cost:", total_cost)


# Driver Code for Adjacency List
prim_list(graph_list, 'A')



# =========================================================
# ADJACENCY MATRIX REPRESENTATION
# =========================================================

# List of vertices
vertices = ['A', 'B', 'C', 'D']

# Graph represented using adjacency matrix
# 0 means no direct edge

graph_matrix = [
    [0, 2, 3, 0],
    [2, 0, 1, 4],
    [3, 1, 0, 5],
    [0, 4, 5, 0]
]


# Prim's Algorithm using Adjacency Matrix
def prim_matrix(graph):

    # Number of vertices
    n = len(graph)

    # Track selected vertices
    selected = [False] * n

    # Start from first vertex
    selected[0] = True

    # Store total cost
    total_cost = 0

    print("\nMST using Adjacency Matrix:\n")

    # MST contains (n - 1) edges
    for _ in range(n - 1):

        # Initialize minimum value
        minimum = float('inf')

        # Store selected edge vertices
        x = 0
        y = 0

        # Traverse matrix
        for i in range(n):

            # Check selected vertices
            if selected[i]:

                for j in range(n):

                    # Find minimum edge
                    # connecting selected and unselected vertex
                    if (
                        not selected[j]
                        and graph[i][j]
                    ):

                        if graph[i][j] < minimum:

                            minimum = graph[i][j]

                            x = i
                            y = j

        # Print selected edge
        print(
            vertices[x],
            "-",
            vertices[y],
            ":",
            graph[x][y]
        )

        # Add edge weight to total cost
        total_cost += graph[x][y]

        # Mark new vertex as selected
        selected[y] = True

    # Print total MST cost
    print("\nTotal Cost:", total_cost)


# Driver Code for Adjacency Matrix
prim_matrix(graph_matrix)

# time complexity: O(E log V) for adjacency list
# time complexity: O(V^2) for adjacency matrix
# space complexity: O(V) for both representations

# NOTE

# Adjacency List and Adjacency Matrix
# are different graph representations.
#
# Therefore, separate implementations are used.
#
# Adjacency List:
# Better for sparse graphs
#
# Adjacency Matrix:
# Better for dense graphs