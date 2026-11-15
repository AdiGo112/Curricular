# Assignment 4: Gradient Descent

## Problem statement
Implement Gradient Descent to find the local minima of a function.

## Approach
`f(x) = (x + 5)^2` is used: a simple convex parabola with a known minimum
at x = -5, f(x) = 0, so the result can be checked exactly. No dataset and
no sklearn are needed -- just the manual update rule:

```
x_new = x_old - learning_rate * gradient(x_old)
```

Each step moves x a little in the direction that decreases f(x) (opposite
to the gradient, since the gradient points toward increasing f). The loop
stops once the gradient is close enough to zero (converged) or a maximum
iteration count is hit, as a safety net against a learning rate that never
converges.

## Implementation notes
- The gradient is the derivative: `d/dx (x + 5)^2 = 2(x + 5)`.
- Start `x = 10`, learning rate `0.1`, tolerance `1e-6`, at most 1000 steps.
- It converges to `x = -5`, `f(x) = 0` after 78 steps.
- Every `x` visited is kept in `path`. The plot `gradient_descent.png` draws
  the curve in blue and the path in red: the steps are large where the curve
  is steep and shrink as it flattens near the minimum, because the step size
  is the learning rate times the gradient.

## Viva prep

**Q: What does the learning rate control, and what happens if it's too
big or too small?**
A: It controls the step size per iteration. Too small converges very
slowly; too large can overshoot the minimum and oscillate or diverge
entirely instead of converging.

**Q: Why does gradient descent here always find the true minimum?**
A: f(x) = (x+5)^2 is convex (a single bowl shape) with exactly one
minimum, so there's no local minimum to get stuck in -- gradient descent
on a convex function is guaranteed to converge to the global minimum.

**Q: How is convergence detected in this implementation?**
A: By checking if the gradient's magnitude has dropped below a small
tolerance (1e-6) -- a near-zero gradient means x is at (or extremely close
to) a minimum.

**Q: Why use a max_iterations cap as well as the tolerance check?**
A: As a safety net -- if the learning rate or function were such that the
gradient never gets small enough, the loop would otherwise run forever.
