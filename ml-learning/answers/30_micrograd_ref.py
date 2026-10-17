"""30. micrograd: the chain rule and a gradient check. A scalar autograd engine, checked against central finite differences.

Modes: --download, --smoke, --baseline (P1), --change (P2), --break (P3), --check.
"""
import inspect
import math
import random
import re
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "labkit.py").exists())))
import labkit  # before numpy, torch, transformers: it sets cache defaults
import torch
args = labkit.start(lab=30, device="cpu", extra_modes=("check",))
H = 1e-6                            # central-difference step, in plain Python floats
REUSE = [("*", 0, 1), ("+", 2, 0)]  # c = a*b + a over inputs (a, b): the second step uses a again

class Value:
    """A scalar that remembers the nodes it was made from, so backward() can apply the chain rule."""
    def __init__(self, data, children=()):
        self.data, self.grad, self._prev, self._backward = data, 0.0, children, lambda: None

    def __add__(self, other):
        out = Value(self.data + other.data, (self, other))
        def _backward():
            self.grad += out.grad
            other.grad += out.grad
        out._backward = _backward
        return out

    # --- CONCEPT start ---
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
    # --- CONCEPT end ---

    def tanh(self):  # --change adds tanh nodes to the expressions; local derivative 1 - tanh^2
        t = math.tanh(self.data)
        out = Value(t, (self,))
        def _backward():
            self.grad += (1 - t * t) * out.grad
        out._backward = _backward
        return out

def with_bug():
    """The break: the same Value class with every '.grad +=' rewritten as '.grad ='."""
    if not labkit.smoke() and not re.search(r"\.grad\s*\+=", inspect.getsource(Value.__mul__)):
        raise SystemExit("--break rewrites each '.grad +=' as '.grad =': write the updates in __mul__ with +=")
    namespace = dict(globals())  # a copy, so this module's own Value stays as written
    exec(re.sub(r"\.grad\s*\+=", ".grad =", inspect.getsource(Value)), namespace)
    return namespace["Value"]

def random_expr(rng, ops, tanh_rng=None):
    """2 to 6 steps over inputs x, y, z drawn from -1 to 1. A + or * step takes the latest node and one earlier node; tanh takes the latest only. With tanh_rng, a tanh node follows each step with probability 1/3, and rng draws exactly what it draws without it."""
    steps, pos = [], [0, 1, 2]  # pos: the index of each node so far; when a tanh node follows a step, later steps use the tanh node
    for _ in range(rng.randint(2, 6)):
        steps.append((rng.choice(ops), pos[-1], pos[rng.randrange(len(pos) - 1)]))
        if tanh_rng and tanh_rng.random() < 1 / 3:
            steps.append(("tanh", len(steps) + 2, len(steps) + 2))
        pos.append(len(steps) + 2)
    return steps, [rng.uniform(-1, 1) for _ in range(3)]

def evaluate(steps, inputs):
    """Run the steps on Values, torch tensors or plain floats, and return the last node."""
    nodes = list(inputs)
    for op, i, j in steps:
        a, b = nodes[i], nodes[j]
        if op == "tanh":
            nodes.append(math.tanh(a) if isinstance(a, float) else a.tanh())
        else:
            nodes.append(a + b if op == "+" else a * b)
    return nodes[-1]

def formula(steps, n_inputs=3):
    """The expression as text over inputs x, y, z (a, b when there are two), for example tanh((z*x))+y."""
    text = list("xyz" if n_inputs == 3 else "ab")
    for op, i, j in steps:
        text.append(f"tanh({text[i]})" if op == "tanh" else f"({text[i]}{op}{text[j]})")
    return text[-1][1:-1] if steps[-1][0] != "tanh" else text[-1]

def torch_grads(steps, xs):
    """Input gradients from torch autograd in float64: the library reference."""
    inputs = [torch.tensor(x, dtype=torch.float64, requires_grad=True) for x in xs]
    evaluate(steps, inputs).backward()
    return [0.0 if t.grad is None else t.grad.item() for t in inputs]

def engine_grads(steps, xs, V):
    """Input gradients from engine V: build the graph, call backward(), read each input's grad."""
    if labkit.smoke():  # smoke checks the plumbing only: torch autograd stands in for the TODO
        return torch_grads(steps, xs)
    inputs = [V(x) for x in xs]
    evaluate(steps, inputs).backward()
    return [v.grad for v in inputs]

def numeric_grad(steps, xs, i):
    """Central difference (f(x + H) - f(x - H)) / 2H for input i, in plain floats."""
    up, down = list(xs), list(xs)
    up[i], down[i] = xs[i] + H, xs[i] - H
    return (evaluate(steps, up) - evaluate(steps, down)) / (2 * H)

def gradient_check(V, tanh=False):
    """log10 of the largest |engine - numeric| gap over 20 random + and * expressions (3 in smoke), and the worst expression. tanh=True adds tanh nodes to the same expressions."""
    rng, tanh_rng, worst = random.Random(42 + args.seed), random.Random(1042 + args.seed), (0.0, "")
    for _ in range(3 if labkit.smoke() else 20):
        steps, xs = random_expr(rng, ("+", "*"), tanh_rng if tanh else None)
        for i, g in enumerate(engine_grads(steps, xs, V)):
            worst = max(worst, (abs(g - numeric_grad(steps, xs, i)), formula(steps)))
    return math.log10(worst[0]), worst[1]

def check():
    """A 20-row fixture (a*b + a, then c*(c + a*b) with c = a*b + a, then 18 random expressions) against torch autograd."""
    rng, ab = random.Random(7), [0.7, -1.3]
    rows = [(REUSE, ab), (REUSE + [("+", 3, 2), ("*", 3, 4)], ab)] + [random_expr(rng, ("+", "*", "tanh")) for _ in range(18)]
    for steps, xs in rows:
        for mine, ref in zip(engine_grads(steps, xs, Value), torch_grads(steps, xs)):
            assert math.isclose(mine, ref, rel_tol=1e-12, abs_tol=1e-12), f"{formula(steps, len(xs))}: {mine} vs torch {ref}"
    print("check: PASS")

if args.mode == "download":
    print("nothing to download: the expressions are synthetic, made at run time")
if args.mode == "check":
    check()
if args.mode in ("smoke", "baseline"):
    labkit.result("P1.log10_max_gap", gradient_check(Value)[0], unit="log10")
    labkit.result("baseline.a_grad", engine_grads(REUSE, [0.7, -1.3], Value)[0])
if args.mode in ("smoke", "change"):
    labkit.result("P2.log10_max_gap", gradient_check(Value, tanh=True)[0], unit="log10")
if args.mode in ("smoke", "break"):
    Buggy = with_bug()
    labkit.result("P3.a_grad", engine_grads(REUSE, [0.7, -1.3], Buggy)[0])
    log_gap, worst = gradient_check(Buggy, tanh=True)
    labkit.result("break.log10_max_gap", log_gap, unit="log10")
    labkit.result("break.worst_expr", worst)
