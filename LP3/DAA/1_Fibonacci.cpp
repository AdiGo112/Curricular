// =====================================================================
// Assignment 1: Fibonacci Numbers (Non-Recursive and Recursive)
// =====================================================================
//
// Problem Statement:
//   Write a program (non-recursive AND recursive) to calculate
//   Fibonacci numbers, find the step count, and analyze their time
//   and space complexity.
//
//   fib(0) = 0, fib(1) = 1, fib(n) = fib(n-1) + fib(n-2) for n >= 2.
//
// Approach:
//   1. Non-Recursive (Iterative): keep only the last two Fibonacci
//      values and update them in a single loop from 2 to n.
//   2. Recursive (Naive): directly translate the recurrence into two
//      recursive calls per non-base case, with NO memoization, so the
//      exponential blow-up of plain recursion is visible.
//
// Complexity:
//   Iterative -> Time: O(n)    Space: O(1)   (two variables only)
//   Recursive -> Time: O(2^n)  Space: O(n)   (call stack depth = n)
//
// Likely Viva Questions:
//   Q1. Why is naive recursive Fibonacci O(2^n)?
//       A. Each call (except base cases) spawns two further calls,
//          forming a binary call tree of depth n, so the total number
//          of calls is bounded by O(2^n).
//   Q2. Why is the recursive version's space O(n), not O(2^n)?
//       A. Space is the deepest single path of the call stack at any
//          instant, not the total calls ever made; only one branch is
//          "live" at a time, so stack depth is n.
//   Q3. How would you speed up the recursive version?
//       A. Add memoization (cache fib(k) results) or switch to the
//          iterative bottom-up approach used here, both O(n) time.
// =====================================================================

#include <iostream>
#include <chrono>
#include <cassert>

using namespace std;

// Counts basic steps: loop iterations (iterative) or function calls (recursive)
long long stepCount = 0;

// 1. NON-RECURSIVE (ITERATIVE) APPROACH
// Time complexity : O(n)  -> single loop from 2 to n
// Space complexity: O(1)  -> only two variables kept, no call stack growth

long long fibIterative(int n) {

    if (n <= 1)
        return n;

    long long prev = 0, curr = 1;

    for (int i = 2; i <= n; i++) {

        stepCount++;
        long long next = prev + curr;
        prev = curr;
        curr = next;
    }

    return curr;
}

// 2. RECURSIVE (NAIVE) APPROACH
// Time complexity : O(2^n) -> each call branches into two more calls
// Space complexity: O(n)   -> recursion call stack depth grows up to n
// Kept naive (no memoization) on purpose, to contrast with the iterative version.

long long fibRecursive(int n) {

    stepCount++;

    if (n <= 1)
        return n;

    return fibRecursive(n - 1) + fibRecursive(n - 2);
}

// Sanity check against a hand-computable value (fib(10) = 55), kept
// separate from whatever the user enters at the prompt in main().
void runSelfTest() {

    assert(fibIterative(10) == 55);
    assert(fibRecursive(10) == 55);
}

// Run one Fibonacci function and report its result plus elapsed time
long long timeCall(long long (*fib)(int), int n, double &elapsedMs, long long &steps) {

    stepCount = 0;
    auto start = chrono::high_resolution_clock::now();
    long long result = fib(n);
    auto end = chrono::high_resolution_clock::now();

    elapsedMs = chrono::duration<double, milli>(end - start).count();
    steps = stepCount;
    return result;
}

int main() {

    runSelfTest();

    // DRIVER CODE
    // Note: the recursive approach is O(2^n), so keep n modest (say, under 35)
    // or it will take a very long time to finish.
    int n;
    cout << "Enter value of n: ";
    cin >> n;

    double timeIterative, timeRecursive;
    long long stepsIterative, stepsRecursive;
    long long resultIterative = timeCall(fibIterative, n, timeIterative, stepsIterative);
    long long resultRecursive = timeCall(fibRecursive, n, timeRecursive, stepsRecursive);

    cout << "\nn = " << n << "\n";
    cout << "  Iterative : fib = " << resultIterative << ", time = " << timeIterative
         << " ms, steps = " << stepsIterative << "\n";
    cout << "  Recursive : fib = " << resultRecursive << ", time = " << timeRecursive
         << " ms, steps = " << stepsRecursive << "\n";

    cout << "\nIterative -> Time: O(n),    Space: O(1)\n";
    cout << "Recursive -> Time: O(2^n),  Space: O(n)  (call stack)\n";

    return 0;
}
