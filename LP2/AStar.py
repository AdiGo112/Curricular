import heapq
import copy


# Goal State
goal = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 0]
]


# Heuristic Function
# Calculates Manhattan Distance
def heuristic(state):

    dist = 0

    for i in range(3):
        for j in range(3):

            val = state[i][j]

            # Ignore empty tile
            if val != 0:

                # Find correct position of tile
                x = (val - 1) // 3
                y = (val - 1) % 3

                # Add Manhattan Distance
                dist += abs(i - x) + abs(j - y)

    return dist


# Find position of empty tile (0)
def find_zero(state):

    for i in range(3):
        for j in range(3):

            if state[i][j] == 0:
                return i, j


# Generate all possible neighboring states
def neighbors(state):

    # Find empty tile position
    x, y = find_zero(state)

    # Possible moves
    moves = [
        (-1, 0),   # Up
        (1, 0),    # Down
        (0, -1),   # Left
        (0, 1)     # Right
    ]

    result = []

    for dx, dy in moves:

        nx = x + dx
        ny = y + dy

        # Check valid move
        if 0 <= nx < 3 and 0 <= ny < 3:

            # Create copy of current state
            new = copy.deepcopy(state)

            # Swap empty tile with neighboring tile
            new[x][y], new[nx][ny] = \
            new[nx][ny], new[x][y]

            # Add new state
            result.append(new)

    return result


# A* Search Algorithm
def astar(start):

    # Priority Queue
    pq = []

    # Add initial state
    heapq.heappush(
        pq,
        (heuristic(start), 0, start)
    )

    # Store visited states
    visited = set()

    while pq:

        # Remove state with minimum cost
        f, g, state = heapq.heappop(pq)

        # Print current state
        print(state)

        # Goal Check
        if state == goal:

            print("Goal Reached")
            return

        # Mark state as visited
        visited.add(tuple(map(tuple, state)))

        # Generate neighboring states
        for n in neighbors(state):

            t = tuple(map(tuple, n))

            # Process only unvisited states
            if t not in visited:

                # Add neighbor to priority queue
                heapq.heappush(
                    pq,
                    (
                        g + 1 + heuristic(n),  # f(n)
                        g + 1,                 # g(n)
                        n
                    )
                )


# Initial State
start = [
    [1, 2, 3],
    [4, 0, 5],
    [6, 7, 8]
]


# Driver Code
astar(start)