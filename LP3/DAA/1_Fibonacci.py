steps = 0


def fib_iterative(n):
    global steps
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
        steps += 1
    return a


def fib_recursive(n):
    global steps
    steps += 1
    if n <= 1:
        return n
    return fib_recursive(n - 1) + fib_recursive(n - 2)


n = int(input("Enter n: "))
for name, fib in [("Iterative", fib_iterative), ("Recursive", fib_recursive)]:
    steps = 0
    print(f"{name}: fib({n}) = {fib(n)}, steps = {steps}")
