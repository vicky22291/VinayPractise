# 30. micrograd: the chain rule and a gradient check: reference answers

> Spoilers. The AI opens one block at a time, only after that step's prediction row exists and the learner pasted their own RESULT lines, or after 'debrief 30'.

`HW chip='Apple M4 Pro' cpu=14 gpu=20 mem_gib=24 macos=26.5.1 python=3.13.7 torch=2.14.1 device=cpu`

- Seeds: 0, 1 and 2 for every step (light lane). Seed S draws its 20 synthetic expressions from `random.Random(42 + S)`, so seed 0 is the spec's seed 42. `--change` and `--break` add tanh nodes to those same expressions, picked by `random.Random(1042 + S)`.
- Reference script: `answers/30_micrograd_ref.py` (script_sha256 b031124edf4657c1). The starter `m5-under-the-hood/scripts/30_micrograd.py` comes from make_c_starter.
- Runs: 9, all current. Wall times for seeds 0, 1 and 2: baseline 1.2, 1.0 and 1.1 s; change 1.3, 1.2 and 1.2 s; break 1.2, 1.1 and 1.3 s. Light lock, 209 to 210 MB peak memory.
- Tolerance rule: tol = spread (max - min) over seeds 0, 1, 2; heavy labs: the baseline spread applies to every step. Spreads and effects below are copied from `answers/30-micrograd.json` and shown to 6 significant digits, the precision of the RESULT lines.
- Raw seed-0 output: `answers/30-micrograd.out`.

<details><summary>P1. Correct engine, + and * only: the largest gap between the engine's gradient and the central finite difference over 20 expressions, as log10</summary>

**Answer:** -9.27906 at seed 0, tolerance ±0.0108 (the seed spread). Seeds 1 and 2 give -9.28986 and -9.28114. In plain numbers, the largest gap is about 5e-10.

```
RESULT P1.log10_max_gap=-9.27906 unit=log10 seed=0
RESULT baseline.a_grad=-0.3 seed=0
```

**Why:** the gap is float64 rounding, not calculus. Each evaluation of f is off by a few times 1e-16 times |f|, and the central difference divides that error by 2h = 2e-6, so the gap grows to about 1e-10 times |f|. Truncation, h^2/6 times f''', is near 1e-12 for these low-degree polynomials, so with outputs of a few units the largest gap lands at a few times 1e-10. The three seeds happen to fall in the same power-of-2 bracket, so the 0.0108 tolerance is narrow by chance; build note 2 gives the 10-seed range.

**Common wrong prediction:** -12 (h squared, the textbook truncation term) or -6 (the step h itself). The truncation term is real but sits below the rounding term at h = 1e-6 in float64. A guess of -16 (machine epsilon) forgets the division by 2h.

</details>

<details><summary>P2. With tanh added: the same largest gap, as log10</summary>

**Answer:** -9.46299 at seed 0, tolerance ±0.31751 (the seed spread). Seeds 1 and 2 give -9.66056 and -9.7805. In plain numbers, the largest gap is about 3e-10. `--change` runs P1's 20 expressions and inputs with tanh nodes added, so each seed compares the same expressions, and P2 is below P1 at all three seeds. The mean shift from P1 is -0.35133, inside 2x the seed spread, so three seeds cannot call it real, and the check stays at the rounding floor.

```
RESULT P2.log10_max_gap=-9.46299 unit=log10 seed=0
```

**Why:** tanh gets an exact local derivative, 1 - tanh^2, so the engine's gradient is off only by its own float64 arithmetic, near 1e-16. The gap is the central difference's error, with the same two parts as in P1: float64 rounding and truncation, h^2/6 times f'''. tanh is not a polynomial, so it adds higher derivatives to f''' and the truncation term can grow. A 50-digit replication of the paired expressions puts the largest truncation at 1.0e-12 to 5.1e-12 over seeds 0 to 2, 68 to 219 times below the measured gaps (build notes, Prototype comparison). So rounding still sets the largest gap, and it stays near 1e-10. That rounding scales with the size of f and of its slope (build note 10), and a tanh node keeps its output within -1 to 1 and its slope at most 1. So values and slopes after a tanh node tend to shrink, which is the likely reason the same expressions give a smaller gap; this run does not isolate that mechanism.

**Common wrong prediction:** a larger gap, because tanh is transcendental or because 1 - tanh^2 loses precision when tanh saturates near ±1. Near saturation both the analytic and the numeric slopes are close to 0, so the absolute gap shrinks rather than grows.

</details>

<details><summary>P3. With = instead of += in _backward: a.grad for c = a*b + a at a = 0.7 and b = -1.3</summary>

**Answer:** -1.3 at every seed, tolerance ±0.0 (the expression has no randomness). The correct engine gives -0.3 (`baseline.a_grad`, which is b + 1), so the bug moves a.grad by -1.0.

```
RESULT P3.a_grad=-1.3 seed=0
RESULT break.log10_max_gap=0.69897 unit=log10 seed=0
RESULT break.worst_expr=(((((z+y)+x)+y)+((z+y)+x))+((z+y)+x))+(((z+y)+x)+y) seed=0
```

Other seeds: `break.log10_max_gap` is 0.194926 and 0.203716 (spread 0.504044), and the worst expressions are `tanh(((tanh((((z+y)+x)*y))+y)+y))` and `((((z+x)*x)*x)+x)+x`.

**Why:** backward() runs each _backward in reverse topological order, so c's add runs first and sets a.grad = 1 for the direct path. Then the a*b node's mul assigns a.grad = b times 1 = -1.3, which wipes out the direct path; with += the two paths add up to b + 1 = -0.3. The gradient check sees the same lost contributions: on the same expressions, the largest gap rises by 10.0006 in log10 over P2 (the mean of the three seeds), from about 1e-10 to order 1. Only an expression that reuses a node loses anything: the seed-0 worst case is all additions and reuses the node (z+y)+x, so every input ends with a gradient of 1 where the true gradients are 4, 6 and 4, a gap of exactly 5 (log10 5 = 0.69897).

**Common wrong prediction:** 1.0, assuming the add's write lands last, or -0.3, assuming the bug only matters in bigger graphs. The order is fixed: the node nearest the output writes first, so the deeper write wins.

</details>

<details><summary>Rebuild check</summary>

- Solution: `answers/rebuild/30_mul_and_backward.py` (19 lines: `__mul__` 7, `backward()` 12). Stub: `m5-under-the-hood/rebuild/30_mul_and_backward.py`.
- `rebuildcheck`: the stub fails as it should (exit 1, NotImplementedError) and the solution passes (exit 0, `check: PASS`). Verdict: REBUILDCHECK OK.
- `check()` runs one function, `expr` = c*(c + m) with m = a*b and c = m + a, on Values, torch tensors and floats at a = 2 and b = -3. Both m and c feed two later nodes, so a `backward()` that runs a node's `_backward` before all of that node's consumers have run gets a wrong gradient.
- On scratch copies the check fails for = in every `_backward`, = in `__mul__` only, swapped local derivatives, a missing grad = 1 seed, forward topological order, breadth-first order, a pre-order walk with a visited set (either child order), a recursion with no visited set and a topological sort with no visited set. Correct engines pass, including ones that run the nodes in another valid order.

</details>

<details><summary>Card drafts</summary>

| ID | Lab | Type | Question |
|---|---|---|---|
| 30-M | 30 | M | In c = a*b + a, a reaches c along two paths. With `.grad =` in every `_backward`, which path's contribution survives in a.grad, and why that one? |
| 30-N | 30 | N | In float64 with h = 1e-6, about how large is the largest gap between a correct engine's gradient and a central finite difference when outputs are a few units, and what sets it? |
| 30-T | 30 | T | A PyTorch training loop never calls `optimizer.zero_grad()`. What gradient does the second update apply, and which rule from this lab explains it? |

Keys:

- 30-M: (1) the a*b path survives: b times out.grad, -1.3 at a = 0.7 and b = -1.3. (2) Reverse topological order runs the add before the mul, so the mul's assignment lands last and overwrites the direct path's 1. (3) += sums both paths: b + 1 = -0.3.
- 30-N: (1) about 1e-10 to 1e-9 (reference, seed 0: log10 -9.27906 with + and *, -9.46299 with tanh). (2) Rounding sets it: about machine epsilon (2.2e-16) times |f|, divided by h. (3) Truncation, h^2/6 times f''', is near 1e-12, so a smaller h makes the gap larger, not smaller.
- 30-T: (1) `backward()` adds into `.grad` with +=, the same accumulation that sums a reused node's paths, and nothing resets it between steps. (2) So step 2 applies step 1's gradient plus its own, and each later step applies the running sum. (3) Frameworks keep += on purpose: summing gradients over micro-batches before one optimizer step is gradient accumulation.

</details>

<details><summary>Build notes</summary>

**Knob changes:** none. Every effect the lab teaches as real exceeds 2x the seed spread: the break's jump in the largest gap (10.0006 in log10 over P2, spread 0.504044) and the bug's shift in a.grad (-1.0, spread 0.0). The change effect (P2 minus P1, mean -0.35133, spread 0.31751) is inside 2x the spread. The lab teaches it as small, because a correctly differentiated op keeps the check at the rounding floor. It is reported with its spread, not inflated and not called zero: on the same expressions, P2 is below P1 at all three seeds (build note 3).

**Precomputed steps:** none. Seed-0 wall times are 1.2 s (baseline), 1.3 s (change) and 1.2 s (break), so the lab's Compute line says 3 runs x 1 min.

**Choices where the spec is silent:**

1. Seeds: expressions come from `random.Random(42 + seed)`, so seed 0 reproduces the spec's seed 42 and seeds 1 and 2 draw new expressions.
2. Generator: 2 to 6 + or * steps over inputs x, y and z drawn uniformly from -1 to 1. Each step combines the latest node with one earlier node, never itself, so reuse is common and repeated squaring cannot blow values up. A tanh node (in `--change`, `--break` and the `--check` fixture) takes the latest node only. A 10-seed design probe in the scratchpad compared generators. With inputs from -2 to 2, one rare expression with outputs in the hundreds or more dominated the maximum, and the 10-seed range of P1 grew past 1.5 in log10 (past 2 when a node may also combine with itself). The chosen generator kept it near 0.5. That is many times P1's 3-seed spread: the three reference seeds happen to share one power-of-2 bracket, so P1's tolerance is narrow by chance.
3. `--change` adds tanh nodes to the baseline's 20 expressions. The + and * steps, their operands and the inputs come from `random.Random(42 + seed)` exactly as in `--baseline`. A second stream, `random.Random(1042 + seed)`, decides after each step, with probability 1/3, whether a tanh node takes that step's result; later steps then use the tanh node. So at each seed P2 and P1 measure the same expressions, and only tanh differs. A structural test in the scratchpad confirmed it at seeds 0 to 2: removing the tanh nodes gives back the baseline's steps and inputs, and without the second stream the generator draws exactly what the first build's did, so P1 and the `--check` fixture are unchanged. The review asked for this. The first build drew new expressions from the op set +, * and tanh with the same seed, which redrew all 20 expressions, so its shift from P1 mixed tanh with the redraw. Paired, P2 is below P1 at all three seeds, but the mean shift is inside 2x the seed spread, so it is reported as small.
4. `--break` rewrites every `.grad +=` in the `Value` class source as `.grad =`: inspect.getsource, a regular expression that accepts any spacing around `+=`, then exec into a copy of the module's globals. So the bug also reaches the learner's own `__mul__`, names the learner imported still resolve, and the module's own `Value` stays correct. Outside smoke it first stops with a message if `__mul__` holds no `.grad +=`. A `__mul__` written as `self.grad = self.grad + ...` would otherwise keep its accumulation and give a P3 that silently disagrees with this file. The lab file tells the learner to write `x.grad += ...`. On scratch copies, `self.grad+=` with no space or with two spaces gets the bug like the reference, a `backward()` that uses a module-level `deque` runs, and the long form stops with the message. The break reruns the check on the `--change` expressions, so its effect on the gap is measured against P2 (the same expressions), not P1.
5. Smoke: torch autograd in float64 stands in for the engine on 3 expressions, so the starter passes `--smoke` with the TODO open.
6. `--check`: a 20-row fixture against torch autograd in float64 at rel_tol and abs_tol 1e-12. On scratch copies, correct engines built several ways (recursive and iterative topological sorts in either child order, Kahn's algorithm, a sort by longest distance from the output) match torch to under 1e-15 in absolute terms, so the margin is wide. The earlier rel_tol of 1e-9 sat within one decade of the P1 and P2 answers, and a learner who read the starter before predicting could anchor on it. Row 1 is c = a*b + a at 0.7 and -1.3. Row 2 is c*(c + a*b) with c = a*b + a at the same point. Then come 18 random expressions over +, * and tanh from fixture seed 7. random_expr always passes the latest node as the first operand, so a pre-order walk down first children visits the step nodes in exact reverse order and passes every random row. Row 2 breaks that pattern: a*b and c each feed two later nodes, and the last step's first operand is not the latest node. Before row 2 was added, a pre-order walk with a visited set passed the fixture and reproduced every reference RESULT value at seeds 0 to 2. On scratch copies the fixture now rejects = in `__mul__`, = in every `_backward`, swapped local derivatives, a missing grad = 1 seed, forward topological order, breadth-first order, a pre-order walk with a visited set (either child order), a recursion with no visited set and a topological sort with no visited set, while correct engines in other valid orders pass. Failure messages name the failing expression, over a and b for the two-input rows.
7. Rebuild check: the spec names c = a*b + a. The check runs `expr` = c*(c + m) with m = a*b and c = m + a, written once and run on Values, torch tensors and floats. It is the same graph as the fixture's row 2, and it rejects the same wrong engines (Rebuild check block). The earlier graph, out = c*c + b, let a pre-order walk and breadth-first order pass. It runs at a = 2.0 and b = -3.0, not at P3's point, so the rebuild never touches a lab result, and it keeps the spec's 1e-5 tolerance against torch and the finite difference.
8. Repo link: the spec lists none. The lab links `hld/payments-risk-decisioning/deep-dives/model-lifecycle-shadow-and-labels.md` section 5 for the Staff follow-up. Its angle is simplest design: the smallest gradient test for CI, and what the shadow stage catches that a unit test cannot. The neighbours use other angles: lab 28 failure modes, lab 29 trade-off, lab 31 migration and lab 32 what pages at 3 am.
9. The third card is T (transfer). The quiz rules alternate T and D from one lab to the next; the build-wide T and D assignment is left to the orchestrator.
10. Error detail behind the P blocks. The step x + h is itself rounded, which adds an error term scaled by |f'| on top of the rounding of f. Both terms come in fixed units: the unit in the last place of f, which doubles each time |f| crosses a power of 2, and the rounded step. Under the bug, the largest gap at each seed is above 1 while the correct engine's stays below 1e-9 on the same expressions, so any tolerance between those flags the buggy engine. Each of the three worst expressions under the bug uses one node in three or more later steps: (z+y)+x feeds 3 at seed 0, the input y feeds 4 at seed 1 and the input x feeds 5 at seed 2.

**Prototype comparison:** the spec carries no `[answers only]` prototype values for this lab, so the runs were compared with first principles. a.grad should be b + 1 = -0.3 with += and b = -1.3 with =, and both came out exactly so. The floor should be about machine epsilon times |f| divided by h, a few times 1e-10 for outputs of a few units, with truncation near 1e-12; the runs give log10 -9.27906 (P1) and -9.46299 (P2) at seed 0. A scratchpad replication of the generator with 50-digit analytic gradients reproduced the three P1 values to the printed digits. It also matched the first build's P2 values. The same replication with exact rationals and an exact h puts the pure truncation error of the P1 expressions at 1e-12 to 2e-12, a few hundred times below the measured gap. The second review asked whether truncation still stays small once tanh makes f non-polynomial. A second scratchpad check copied the reference's engine and generator, reproduced all six P1 and P2 values to the printed digits, and redid each central difference in 50-digit arithmetic, which removes the rounding. It gives the same 1.0e-12 to 2.0e-12 for P1, and 1.0e-12 to 5.1e-12 for the paired P2 expressions, 68 to 219 times below P2's measured gaps. So rounding, not truncation, sets the largest gap in both steps. No direction or size conflict. The fix round changed the script (fixture row 2, `with_bug()`, `formula()` input names), and the final check changed it again (the `random_expr` docstring and the fixture tolerance). All 9 runs were redone each time, and every RESULT value matched the earlier runs exactly. The review fix (build note 3) changed the `--change` and `--break` expressions, and all 9 runs were redone again: P1, `baseline.a_grad` and `P3.a_grad` match the earlier runs exactly, while P2 and the break values changed with the expressions. The second review's fix changed only this file's text, so no run was redone.

</details>
