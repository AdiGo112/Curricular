# GRAPH COLORING PROBLEM
# Using:
# 1. Backtracking
# 2. Branch and Bound


# FUNCTION TO CHECK SAFE COLOR

def is_safe(vertex, graph, color, c, V):

    # Check adjacent vertices
    for i in range(V):

        # If adjacent vertex has same color
        if graph[vertex][i] == 1 \
           and color[i] == c:

            return False

    return True



# =========================================================
# 1. BACKTRACKING APPROACH
# =========================================================

# Recursive function
def solve_backtracking(vertex,
                       graph,
                       m,
                       color,
                       V):

    # Base Case
    if vertex == V:

        return True

    # Try all colors
    for c in range(1, m + 1):

        # Check safe color
        if is_safe(
            vertex,
            graph,
            color,
            c,
            V
        ):

            # Assign color
            color[vertex] = c

            # Recursive call
            if solve_backtracking(
                vertex + 1,
                graph,
                m,
                color,
                V
            ):

                return True

            # Backtracking
            color[vertex] = 0

    return False


# Function to start backtracking
def graph_coloring_backtracking(graph,
                                m,
                                V):

    # Store colors
    color = [0] * V

    # Solve problem
    if not solve_backtracking(
        0,
        graph,
        m,
        color,
        V
    ):

        print("No Solution Exists")

        return

    # Print solution
    print("Assigned Colors:\n")

    for i in range(V):

        print(
            "Vertex",
            i,
            "-> Color",
            color[i]
        )


# 2. BRANCH AND BOUND APPROACH

# Recursive function
def solve_branch_bound(vertex,
                       graph,
                       m,
                       color,
                       V):

    # Base Case
    if vertex == V:

        return True

    # Try colors
    for c in range(1, m + 1):

        bound = True

        # Bounding condition
        for i in range(V):

            if graph[vertex][i] == 1 \
               and color[i] == c:

                bound = False
                break

        # If safe
        if bound:

            # Assign color
            color[vertex] = c

            # Recursive call
            if solve_branch_bound(
                vertex + 1,
                graph,
                m,
                color,
                V
            ):

                return True

            # Backtracking
            color[vertex] = 0

    return False


# Function to start Branch and Bound
def graph_coloring_branch_bound(
    graph,
    m,
    V
):

    # Store colors
    color = [0] * V

    # Solve problem
    if not solve_branch_bound(
        0,
        graph,
        m,
        color,
        V
    ):

        print("No Solution Exists")

        return

    # Print solution
    print("Assigned Colors:\n")

    for i in range(V):

        print(
            "Vertex",
            i,
            "-> Color",
            color[i]
        )



# =========================================================
# DRIVER CODE
# =========================================================

# Number of vertices
V = 4

# Graph using adjacency matrix
graph = [

    [0, 1, 1, 1],

    [1, 0, 1, 0],

    [1, 1, 0, 1],

    [1, 0, 1, 0]
]

# Number of colors
m = 3


# ---------- Backtracking ----------
print("\nBacktracking Approach \n")
graph_coloring_backtracking(
    graph,
    m,
    V
)


# ---------- Branch and Bound ----------
print("\nBranch and Bound Approach \n")
graph_coloring_branch_bound(
    graph,
    m,
    V
)