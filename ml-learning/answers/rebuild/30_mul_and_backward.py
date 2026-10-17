"""Rebuild 30: Value.__mul__ and Value.backward() from memory.

__init__ and __add__ are given as the pattern. Write the two bodies, then run
python rebuild/30_mul_and_backward.py. check() compares your gradients with torch
autograd and a central finite difference; it never uses this lab's results.
"""
import torch


class Value:
    def __init__(self, data, children=()):
        self.data, self.grad, self._prev, self._backward = data, 0.0, children, lambda: None

    def __add__(self, other):
        out = Value(self.data + other.data, (self, other))

        def _backward():
            self.grad += out.grad
            other.grad += out.grad
        out._backward = _backward
        return out

    def __mul__(self, other):
        """Return a node for self * other whose _backward adds each input's local derivative times out.grad."""
        out = Value(self.data * other.data, (self, other))

        def _backward():
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad
        out._backward = _backward
        return out

    def backward(self):
        """Sort the graph so every node comes after its inputs, set self.grad = 1, then run each _backward from the output back."""
        topo, seen = [], set()

        def build(v):
            if v not in seen:
                seen.add(v)
                for child in v._prev:
                    build(child)
                topo.append(v)
        build(self)
        self.grad = 1.0
        for v in reversed(topo):
            v._backward()


def numeric_grad(f, x, h=1e-6):
    """Central difference (f(x + h) - f(x - h)) / 2h."""
    return (f(x + h) - f(x - h)) / (2 * h)


def expr(x, y):
    """c = x*y + x uses x twice; m = x*y and c each feed two later nodes. Runs on Values, torch tensors or floats."""
    m = x * y
    c = m + x
    return c * (c + m)


def check():
    """Compare a.grad and b.grad for expr at a = 2 and b = -3 with torch autograd and central finite differences."""
    a, b = Value(2.0), Value(-3.0)
    expr(a, b).backward()
    ta = torch.tensor(2.0, dtype=torch.float64, requires_grad=True)
    tb = torch.tensor(-3.0, dtype=torch.float64, requires_grad=True)
    expr(ta, tb).backward()
    assert abs(a.grad - ta.grad.item()) < 1e-5 and abs(b.grad - tb.grad.item()) < 1e-5, "differs from torch autograd"
    assert abs(a.grad - numeric_grad(lambda x: expr(x, -3.0), 2.0)) < 1e-5, "a.grad differs from the finite difference"
    assert abs(b.grad - numeric_grad(lambda y: expr(2.0, y), -3.0)) < 1e-5, "b.grad differs from the finite difference"
    print("check: PASS")


if __name__ == "__main__":
    check()
