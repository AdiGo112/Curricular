#include <iostream>
using namespace std;

long long steps;

long long fibIterative(int n) {
    long long a = 0, b = 1;
    for (int i = 0; i < n; i++) {
        long long next = a + b;
        a = b;
        b = next;
        steps++;
    }
    return a;
}

long long fibRecursive(int n) {
    steps++;
    if (n <= 1) return n;
    return fibRecursive(n - 1) + fibRecursive(n - 2);
}

int main() {
    int n;
    cout << "Enter n: ";
    cin >> n;

    steps = 0;
    long long value = fibIterative(n);
    cout << "Iterative: fib(" << n << ") = " << value << ", steps = " << steps << "\n";

    steps = 0;
    value = fibRecursive(n);
    cout << "Recursive: fib(" << n << ") = " << value << ", steps = " << steps << "\n";
}
