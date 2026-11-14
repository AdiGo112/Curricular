# Assignment 1: Fibonacci Numbers

## Problem statement
Write a non-recursive and a recursive program to calculate Fibonacci numbers,
find the step count, and analyze their time and space complexity.

## Approach
`fib(0) = 0`, `fib(1) = 1`, `fib(n) = fib(n-1) + fib(n-2)`.

- **Iterative**: keep only the last two values and roll them forward `n` times.
- **Recursive**: call `fib(n-1)` and `fib(n-2)` directly. No memoization, on
  purpose, so the exponential blow-up is visible.

## Step count
A global counter `steps` is reset before each run.

- Iterative: one step per loop iteration, so `n` steps.
- Recursive: one step per function call. The call count follows
  `T(n) = T(n-1) + T(n-2) + 1`, which grows as fast as Fibonacci itself.

| n | Iterative steps | Recursive steps |
| --- | --- | --- |
| 5 | 5 | 15 |
| 8 | 8 | 67 |
| 20 | 20 | 21891 |

## Complexity

| Version | Time | Space |
| --- | --- | --- |
| Iterative | O(n) | O(1) |
| Recursive | O(2^n) | O(n), the depth of the call stack |

## Viva prep

**Q: Why is the recursive version so slow?**
A: It recomputes the same subproblems again and again. `fib(n-2)` is computed
once directly and once more inside `fib(n-1)`, and this repeats at every level.

**Q: How would you fix it?**
A: Memoization (store each `fib(k)` once) or the iterative version. Both bring
the time down to O(n).

**Q: Why is recursive space O(n) and not O(2^n)?**
A: Only one branch of the call tree is on the stack at a time, and the deepest
branch has `n` frames.
