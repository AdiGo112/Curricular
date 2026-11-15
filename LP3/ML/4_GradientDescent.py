from pathlib import Path

import matplotlib.pyplot as plt


def f(x):
    return (x + 5) ** 2


def gradient(x):
    return 2 * (x + 5)


learning_rate = 0.1
path = [10.0]

for _ in range(1000):
    x = path[-1]
    if abs(gradient(x)) < 1e-6:
        break
    path.append(x - learning_rate * gradient(x))

print(f"Minimum at x = {x:.4f}, f(x) = {f(x):.4f}, after {len(path) - 1} steps")

curve = [i / 10 for i in range(-200, 101)]
plt.figure()
plt.plot(curve, [f(c) for c in curve])
plt.plot(path, [f(p) for p in path], "ro-")
plt.xlabel("x")
plt.ylabel("f(x)")
plt.savefig(Path(__file__).parent / "gradient_descent.png")
plt.show()
