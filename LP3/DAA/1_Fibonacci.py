# Assignment 1: Fibonacci numbers, non-recursive and recursive.
#
# Problem Statement:
#   Write a program (non-recursive AND recursive) to calculate
#   Fibonacci numbers, find the step count, and analyze their time
#   and space complexity.
#
# fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2)
#
# Iterative: O(n) time, O(1) space (keeps only the last two values).
# Recursive: O(2^n) time, O(n) space (call stack depth = n), no
# memoization on purpose so the exponential blow-up is visible.


def fib_iterative(n):
    if n <= 1:
        return n
    prev, curr = 0, 1
    for _ in range(2, n + 1):
        prev, curr = curr, prev + curr
    return curr


def fib_recursive(n):
    if n <= 1:
        return n
    return fib_recursive(n - 1) + fib_recursive(n - 2)


n = int(input("Enter value of n: "))

print(f"Iterative: {fib_iterative(n)}  (Time: O(n), Space: O(1))")
print(f"Recursive: {fib_recursive(n)}  (Time: O(2^n), Space: O(n))")
