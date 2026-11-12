// Assignment 1: Fibonacci numbers, non-recursive and recursive.
//
// Problem Statement:
//   Write a program (non-recursive AND recursive) to calculate
//   Fibonacci numbers, find the step count, and analyze their time
//   and space complexity.
//
// fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2)
//
// Iterative: O(n) time, O(1) space (keeps only the last two values).
// Recursive: O(2^n) time, O(n) space (call stack depth = n), no
// memoization on purpose so the exponential blow-up is visible.

#include <iostream>
using namespace std;

long long fibIterative(int n) {
    if (n <= 1) return n;
    long long prev = 0, curr = 1;
    for (int i = 2; i <= n; i++) {
        long long next = prev + curr;
        prev = curr;
        curr = next;
    }
    return curr;
}

long long fibRecursive(int n) {
    if (n <= 1) return n;
    return fibRecursive(n - 1) + fibRecursive(n - 2);
}

int main() {
    int n;
    cout << "Enter value of n: ";
    cin >> n;

    cout << "Iterative: " << fibIterative(n) << "  (Time: O(n), Space: O(1))\n";
    cout << "Recursive: " << fibRecursive(n) << "  (Time: O(2^n), Space: O(n))\n";
    return 0;
}
