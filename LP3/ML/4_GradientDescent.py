def f(x):
    return (x + 5) ** 2


def gradient(x):
    return 2 * (x + 5)


x = 10.0
learning_rate = 0.1

for step in range(1000):
    if abs(gradient(x)) < 1e-6:
        break
    x -= learning_rate * gradient(x)

print(f"Minimum at x = {x:.4f}, f(x) = {f(x):.4f}, after {step} steps")
