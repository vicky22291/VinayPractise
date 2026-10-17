import os
import random
import subprocess
import sys
import textwrap
import unittest
from datetime import date, timedelta

from recon.matcher import Reconciler, reconcile

INVOICES = ["INV-1,300,2024-04-01", "INV-2,500,2024-05-01", "INV-3,200,2024-06-01"]


def reference(payments, invoices, tolerance):
    """Slow, obviously correct version of Parts 1 to 4. Used to check the fast one."""
    invs = []
    for pos, line in enumerate(invoices):
        i, a, d = line.split(",")
        invs.append((i, int(a), date.fromisoformat(d), pos))
    by_id = {x[0]: x for x in invs}
    closed, out = set(), []
    import re
    for line in payments:
        pid, amount, memo = line.split(",", 2)
        amount = int(amount)
        ids = list(dict.fromkeys(re.findall(r"(?<![\w-])INV-\d+(?!\d)", memo)))
        named = [by_id[i] for i in ids if i in by_id and i not in closed]
        head = f"payment {pid} (amount {amount})"
        if len(named) > 1 and sum(x[1] for x in named) == amount:
            closed.update(x[0] for x in named)
            out.append(f"{head} pays invoices " + ", ".join(f"{x[0]} due {x[2].isoformat()}" for x in named))
            continue
        if named:
            x = named[0]
        else:
            cands = [x for x in invs if x[0] not in closed and abs(x[1] - amount) <= tolerance]
            x = min(cands, key=lambda c: (abs(c[1] - amount), c[2], c[3])) if cands else None
        if x is None:
            out.append(f"{head} has no matching invoice")
            continue
        closed.add(x[0])
        line = f"{head} pays invoice {x[0]} due {x[2].isoformat()}"
        if not named and x[1] > amount:
            line += f" (forgiven {x[1] - amount})"
        elif not named and x[1] < amount:
            line += f" (overpaid {amount - x[1]})"
        out.append(line)
    return out


def random_batch(seed, n_invoices, n_payments):
    rng = random.Random(seed)
    start = date(2024, 1, 1)
    invoices = [f"INV-{i},{rng.randint(1, 3000)},{start + timedelta(days=rng.randint(0, 90))}" for i in range(n_invoices)]
    payments = []
    for p in range(n_payments):
        kind = rng.random()
        amount = rng.randint(1, 3000)
        if kind < 0.3:
            memo = f"Paying INV-{rng.randrange(n_invoices)}"
        elif kind < 0.4:
            memo = f"INV-{rng.randrange(n_invoices)}, INV-{rng.randrange(n_invoices)}"
        else:
            memo = rng.choice(["", "thanks", "monthly, fees"])
        payments.append(f"p{p},{amount},{memo}")
    return invoices, payments


class Part5(unittest.TestCase):
    def test_run_matches_reconcile(self):
        payments = ["p1,300,", "p2,700,INV-2 INV-3"]
        self.assertEqual(Reconciler(INVOICES).run("b1", payments), reconcile(payments, INVOICES))

    def test_state_carries_across_batches(self):
        r = Reconciler(INVOICES)
        r.run("b1", ["p1,300,"])
        self.assertEqual(r.run("b2", ["p2,300,INV-1"]), ["payment p2 (amount 300) has no matching invoice"])

    def test_rerun_same_batch_is_a_no_op(self):
        r = Reconciler(INVOICES)
        first = r.run("b1", ["p1,300,", "p2,500,"])
        self.assertEqual(r.run("b1", ["p1,300,", "p2,500,"]), first)
        self.assertEqual(r.run("b2", ["p3,200,"]), ["payment p3 (amount 200) pays invoice INV-3 due 2024-06-01"])

    def test_same_batch_id_different_payments(self):
        r = Reconciler(INVOICES)
        r.run("b1", ["p1,300,"])
        with self.assertRaises(ValueError):
            r.run("b1", ["p1,300,", "p9,1,"])

    def test_payment_resent_in_new_batch(self):
        r = Reconciler(["INV-1,300,2024-04-01", "INV-2,300,2024-05-01"])
        first = r.run("b1", ["p1,300,"])
        self.assertEqual(r.run("b2", ["p1,300,", "p2,300,"]),
                         first + ["payment p2 (amount 300) pays invoice INV-2 due 2024-05-01"])

    def test_duplicate_payment_in_one_batch(self):
        r = Reconciler(["INV-1,300,2024-04-01", "INV-2,300,2024-05-01"])
        out = r.run("b1", ["p1,300,", "p1,300,", "p2,300,"])
        self.assertEqual(out[0], out[1])
        self.assertEqual(out[2], "payment p2 (amount 300) pays invoice INV-2 due 2024-05-01")

    def test_tolerance_in_constructor(self):
        r = Reconciler(["INV-1,300,2024-04-01"], tolerance=5)
        self.assertEqual(r.run("b1", ["p1,296,"]), ["payment p1 (amount 296) pays invoice INV-1 due 2024-04-01 (forgiven 4)"])

    def test_matches_reference_on_random_batches(self):
        for seed in range(5):
            invoices, payments = random_batch(seed, 300, 400)
            with self.subTest(seed=seed):
                self.assertEqual(reconcile(payments, invoices, tolerance=7), reference(payments, invoices, 7))

    def test_scale(self):
        # 50k x 50k with tolerance. A full scan per payment is ~2.5e9 steps: over a minute.
        # The indexed answer key takes well under a second. Budget is 20 s.
        script = textwrap.dedent("""
            import sys
            sys.path.insert(0, %r)
            from test_p5_scale import random_batch
            from recon.matcher import reconcile
            invoices, payments = random_batch(42, 50000, 50000)
            print(len(reconcile(payments, invoices, tolerance=25)))
        """ % os.path.dirname(os.path.abspath(__file__)))
        try:
            p = subprocess.run([sys.executable, "-c", script], cwd=os.getcwd(), capture_output=True, text=True, timeout=20)
        except subprocess.TimeoutExpired:
            self.fail("50,000 payments x 50,000 invoices took over 20 s")
        self.assertEqual(p.returncode, 0, p.stderr[-2000:])
        self.assertEqual(p.stdout.strip(), "50000")


if __name__ == "__main__":
    unittest.main()
