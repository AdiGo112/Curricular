# DAA: Design and Analysis of Algorithms

LP3 Group A. Group B (Machine Learning), Group C (Blockchain) and item 6 (mini project) are out of scope here.

**Study notes:** each file starts with a header comment covering the problem statement, approach, time/space complexity and likely viva questions; the body is commented step by step.

| # | Assignment | Files |
| --- | --- | --- |
| 1 | Fibonacci numbers, non-recursive and recursive, with time/space complexity analysis | `1_Fibonacci.cpp`, `1_Fibonacci.py` |
| 2 | Huffman Encoding using a greedy strategy | `2_HuffmanEncoding.cpp`, `2_HuffmanEncoding.py` |
| 3 | Fractional Knapsack using a greedy method | `3_FractionalKnapsack.cpp`, `3_FractionalKnapsack.py` |
| 4 | 0-1 Knapsack using dynamic programming | `4_ZeroOneKnapsack.cpp`, `4_ZeroOneKnapsack.py` |
| 5 | N-Queens with the first Queen already placed, remaining queens via backtracking | `5_NQueens.cpp`, `5_NQueens.py` |

## How to run

No external libraries are needed (C++: standard headers only; Python: standard library only).

```bash
# C++
g++ -std=c++17 -O2 1_Fibonacci.cpp -o a.out && ./a.out

# Python
python 1_Fibonacci.py
```

Same pattern for files 2 to 5. Every program prompts for its own input at runtime (size, string, items, capacity, etc.) and also runs a quick `assert`-based sanity check against a hand-calculated sample before asking for input.
