"""
Assignment 4: Gradient Descent
===============================

Problem statement
------------------
Implement Gradient Descent to find the local minima of a function.

Approach
--------
f(x) = (x + 5)^2 is used: a simple convex parabola with a known minimum at
x = -5, f(x) = 0, so the result can be checked exactly. No dataset and no
sklearn are needed -- just the manual update rule:

    x_new = x_old - learning_rate * gradient(x_old)

Each step moves x a little in the direction that decreases f(x) (opposite
to the gradient, since the gradient points toward increasing f). The loop
stops once the gradient is close enough to zero (converged) or a maximum
iteration count is hit, as a safety net against a learning rate that never
converges.

Likely viva questions
----------------------
Q: What does the learning rate control, and what happens if it's too big
   or too small?
A: It controls the step size per iteration. Too small converges very
   slowly; too large can overshoot the minimum and oscillate or diverge
   entirely instead of converging.

Q: Why does gradient descent here always find the true minimum?
A: f(x) = (x+5)^2 is convex (a single bowl shape) with exactly one minimum,
   so there's no local minimum to get stuck in -- gradient descent on a
   convex function is guaranteed to converge to the global minimum.

Q: How is convergence detected in this implementation?
A: By checking if the gradient's magnitude has dropped below a small
   tolerance (1e-6) -- a near-zero gradient means x is at (or extremely
   close to) a minimum.

Q: Why use a max_iterations cap as well as the tolerance check?
A: As a safety net -- if the learning rate or function were such that the
   gradient never gets small enough, the loop would otherwise run forever.
"""


def f(x):
    return (x + 5) ** 2


def gradient(x):
    # d/dx (x+5)^2 = 2(x+5)
    return 2 * (x + 5)


def gradient_descent(start_x, learning_rate=0.1, max_iterations=1000, tolerance=1e-6):
    x = start_x
    history = []

    for i in range(max_iterations):
        grad = gradient(x)
        history.append((i, x, f(x), grad))

        # Stop once the gradient is practically flat (converged). The
        # max_iterations cap is a safety net in case it never gets this small.
        if abs(grad) < tolerance:
            break

        # Step opposite the gradient (which points toward increasing f),
        # scaled by learning_rate -- too big overshoots, too small is slow.
        x = x - learning_rate * grad

    return x, history


if __name__ == "__main__":
    final_x, history = gradient_descent(start_x=10.0, learning_rate=0.1)

    print(f"{'Iter':<6}{'x':>12}{'f(x)':>12}{'gradient':>12}")
    for i, x, fx, grad in history[:10]:
        print(f"{i:<6}{x:>12.5f}{fx:>12.5f}{grad:>12.5f}")
    if len(history) > 10:
        print(f"... ({len(history)} iterations total)")

    print(f"\nConverged to x = {final_x:.6f}, f(x) = {f(final_x):.6f}")
    print("Known minimum: x = -5, f(x) = 0")
