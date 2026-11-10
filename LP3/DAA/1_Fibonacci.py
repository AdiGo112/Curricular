# =====================================================================
# Assignment 1: Fibonacci Numbers (Non-Recursive and Recursive)
# =====================================================================
#
# Problem Statement:
#   Write a program (non-recursive AND recursive) to calculate
#   Fibonacci numbers, find the step count, and analyze their time
#   and space complexity.
#
#   fib(0) = 0, fib(1) = 1, fib(n) = fib(n-1) + fib(n-2) for n >= 2.
#
# Approach:
#   1. Non-Recursive (Iterative): keep only the last two Fibonacci
#      values and update them in a single loop from 2 to n.
#   2. Recursive (Naive): directly translate the recurrence into two
#      recursive calls per non-base case, with NO memoization, so the
#      exponential blow-up of plain recursion is visible.
#
# Complexity:
#   Iterative -> Time: O(n)    Space: O(1)   (two variables only)
#   Recursive -> Time: O(2^n)  Space: O(n)   (call stack depth = n)
#
# Likely Viva Questions:
#   Q1. Why is naive recursive Fibonacci O(2^n)?
#       A. Each call (except base cases) spawns two further calls,
#          forming a binary call tree of depth n, so the total number
#          of calls is bounded by O(2^n).
#   Q2. Why is the recursive version's space O(n), not O(2^n)?
#       A. Space is the deepest single path of the call stack at any
#          instant, not the total calls ever made; only one branch is
#          "live" at a time, so stack depth is n.
#   Q3. How would you speed up the recursive version?
#       A. Add memoization (cache fib(k) results) or switch to the
#          iterative bottom-up approach used here, both O(n) time.
# =====================================================================

import time

# Counts basic steps: loop iterations (iterative) or function calls (recursive)
step_count = 0


# 1. NON-RECURSIVE (ITERATIVE) APPROACH

# Time complexity : O(n)  -> single loop from 2 to n
# Space complexity: O(1)  -> only two variables kept, no call stack growth

def fib_iterative(n):

    global step_count

    if n <= 1:
        return n

    prev, curr = 0, 1

    for _ in range(2, n + 1):
        step_count += 1
        prev, curr = curr, prev + curr

    return curr


# 2. RECURSIVE (NAIVE) APPROACH

# Time complexity : O(2^n) -> each call branches into two more calls
# Space complexity: O(n)   -> recursion call stack depth grows up to n
# Kept naive (no memoization) on purpose, to contrast with the iterative version.

def fib_recursive(n):

    global step_count
    step_count += 1

    if n <= 1:
        return n

    return fib_recursive(n - 1) + fib_recursive(n - 2)


# DRIVER CODE

# Sanity check against a hand-computable value, kept separate from
# whatever the user enters at the input() prompt below.
# fib(10) = 55, verified by hand: 0,1,1,2,3,5,8,13,21,34,55
def run_self_test():
    assert fib_iterative(10) == 55
    assert fib_recursive(10) == 55


# Run one Fibonacci function and report its result plus elapsed time
def timed_call(fib, n):
    global step_count
    step_count = 0
    start = time.time()
    result = fib(n)
    elapsed_ms = (time.time() - start) * 1000
    return result, elapsed_ms, step_count


run_self_test()

# Note: the recursive approach is O(2^n), so keep n modest (say, under 35)
# or it will take a very long time to finish.
n = int(input("Enter value of n: "))

result_iterative, time_iterative, steps_iterative = timed_call(fib_iterative, n)
result_recursive, time_recursive, steps_recursive = timed_call(fib_recursive, n)

print(f"\nn = {n}")
print(f"  Iterative : fib = {result_iterative}, time = {time_iterative:.4f} ms, steps = {steps_iterative}")
print(f"  Recursive : fib = {result_recursive}, time = {time_recursive:.4f} ms, steps = {steps_recursive}")

print("\nIterative -> Time: O(n),    Space: O(1)")
print("Recursive -> Time: O(2^n),  Space: O(n)  (call stack)")
