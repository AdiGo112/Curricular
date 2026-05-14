# KRUSKAL'S MINIMUM SPANNING TREE ALGORITHM

# GRAPH REPRESENTATION USING EDGE LIST
# Format:
# (Weight, Vertex1, Vertex2)

graph = [
    (1, 'B', 'C'),
    (2, 'A', 'B'),
    (3, 'A', 'C'),
    (4, 'B', 'D'),
    (5, 'C', 'D')
]


# DISJOINT SET (UNION-FIND)
# Store parent of each vertex
parent = {}

# Store rank of each vertex
rank = {}


# Create separate set for each vertex
def make_set(vertices):

    for vertex in vertices:

        parent[vertex] = vertex
        rank[vertex] = 0


# Find parent/root of a vertex
def find(vertex):

    # Path Compression
    if parent[vertex] != vertex:

        parent[vertex] = find(parent[vertex])

    return parent[vertex]


# Union two sets
def union(v1, v2):

    root1 = find(v1)
    root2 = find(v2)

    # Union by Rank
    if rank[root1] < rank[root2]:

        parent[root1] = root2

    elif rank[root1] > rank[root2]:

        parent[root2] = root1

    else:

        parent[root2] = root1
        rank[root1] += 1

# KRUSKAL'S ALGORITHM

def kruskal(graph):

    mst = []

    total_cost = 0

    # Get all vertices
    vertices = set()

    for weight, u, v in graph:

        vertices.add(u)
        vertices.add(v)

    # Initialize disjoint sets
    make_set(vertices)

    # Sort edges according to weight
    graph.sort()

    # Traverse sorted edges
    for weight, u, v in graph:

        # Check for cycle
        if find(u) != find(v):

            # Add edge to MST
            mst.append((u, v, weight))

            # Add edge cost
            total_cost += weight

            # Merge sets
            union(u, v)

    # Print MST
    print("Edges in MST:\n")

    for u, v, weight in mst:

        print(u, "-", v, ":", weight)

    print("\nTotal Cost:", total_cost)


# DRIVER CODE
kruskal(graph)

# time complexity: O(E log E) due to sorting edges
# space complexity: O(V) for disjoint set data structure