import heapq

# DIJKSTRA'S SINGLE SOURCE SHORTEST PATH ALGORITHM

# GRAPH USING ADJACENCY LIST
# Format:
# Vertex : [(Neighbor, Weight)]

graph = {
    'A': [('B', 2), ('C', 4)],
    'B': [('A', 2), ('C', 1), ('D', 7)],
    'C': [('A', 4), ('B', 1), ('D', 3)],
    'D': [('B', 7), ('C', 3)]
}

# DIJKSTRA'S ALGORITHM

def dijkstra(graph, start):

    # Store shortest distances
    distances = {}

    # Initialize all distances as infinity
    for vertex in graph:
        distances[vertex] = float('inf')

    # Distance of starting vertex is 0
    distances[start] = 0

    # Priority Queue / Min Heap
    # Stores (distance, vertex)
    pq = [(0, start)]

    # Continue until queue becomes empty
    while pq:

        # Remove minimum distance vertex
        current_distance, current_vertex = \
        heapq.heappop(pq)

        # Traverse neighboring vertices
        for neighbor, weight in graph[current_vertex]:

            # Calculate new distance
            distance = current_distance + weight

            # Update shorter distance
            if distance < distances[neighbor]:

                distances[neighbor] = distance

                # Add updated distance to heap
                heapq.heappush(
                    pq,
                    (distance, neighbor)
                )

    # Print shortest distances
    print("Shortest Distances from", start, ":\n")

    for vertex in distances:

        print(
            start,
            "->",
            vertex,
            "=",
            distances[vertex]
        )


# DRIVER CODE

dijkstra(graph, 'A')

# time complexity: O((V + E) log V) due to priority queue operations
# space complexity: O(V) for storing distances and priority queue