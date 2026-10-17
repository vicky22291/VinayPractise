import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal

from invoicing.money import Money

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def run_suite(root):
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."]
    return subprocess.run(cmd, cwd=root, env=ENV, capture_output=True, text=True, timeout=300)


def with_pr_file(name):
    """Copy the run dir, put back the PR's original invoicing/<name>, run the candidate's suite."""
    with tempfile.TemporaryDirectory() as tmp:
        root = os.path.join(tmp, "run")
        shutil.copytree(os.getcwd(), root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        shutil.copy(os.path.join(FIXTURES, f"pr_{name}"), os.path.join(root, "invoicing", name))
        return run_suite(root)


class SuiteCatchesThePR(unittest.TestCase):
    def test_suite_passes_on_your_code(self):
        r = run_suite(os.getcwd())
        self.assertEqual(r.returncode, 0, r.stdout[-1500:] + r.stderr[-1500:])

    def test_suite_fails_on_pr_processor(self):
        self.assertNotEqual(with_pr_file("processor.py").returncode, 0, "your tests pass on the PR's processor.py")

    def test_suite_fails_on_pr_totals(self):
        self.assertNotEqual(with_pr_file("totals.py").returncode, 0, "your tests pass on the PR's totals.py")


class MoneyType(unittest.TestCase):
    def test_construct(self):
        m = Money(1999, "usd")
        self.assertEqual((m.amount, m.currency), (1999, "usd"))

    def test_rejects_float_and_bool(self):
        for bad in (19.99, 1999.0, True):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    Money(bad, "usd")

    def test_rejects_unknown_currency(self):
        with self.assertRaises(ValueError):
            Money(100, "xyz")

    def test_from_major(self):
        self.assertEqual(Money.from_major("19.99", "usd"), Money(1999, "usd"))
        self.assertEqual(Money.from_major("19.9", "usd"), Money(1990, "usd"))
        self.assertEqual(Money.from_major(Decimal("1.234"), "kwd"), Money(1234, "kwd"))
        self.assertEqual(Money.from_major("4650", "jpy"), Money(4650, "jpy"))

    def test_from_major_rejects(self):
        with self.assertRaises(TypeError):
            Money.from_major(19.99, "usd")
        with self.assertRaises(ValueError):
            Money.from_major("1.5", "jpy")
        with self.assertRaises(ValueError):
            Money.from_major("1.999", "usd")

    def test_arithmetic(self):
        self.assertEqual(Money(1000, "usd") + Money(999, "usd"), Money(1999, "usd"))
        self.assertEqual(Money(1000, "usd") - Money(1, "usd"), Money(999, "usd"))
        self.assertEqual(Money(500, "jpy") * 3, Money(1500, "jpy"))

    def test_arithmetic_rejects(self):
        with self.assertRaises(ValueError):
            Money(1, "usd") + Money(1, "eur")
        with self.assertRaises(TypeError):
            Money(1, "usd") + 1
        with self.assertRaises(TypeError):
            Money(1, "usd") * 1.5

    def test_str(self):
        self.assertEqual(str(Money(4650, "jpy")), "4650 JPY")
        self.assertEqual(str(Money(1999, "usd")), "19.99 USD")


if __name__ == "__main__":
    unittest.main()
