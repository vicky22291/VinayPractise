import os
import subprocess
import sys
import tempfile
import unittest

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def lint(target):
    tool = os.path.join(os.getcwd(), "tools", "no_float_money.py")
    return subprocess.run([sys.executable, tool, target], capture_output=True, text=True, timeout=60)


def lint_source(src):
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "mod.py"), "w") as f:
            f.write(src)
        return lint(tmp)


class Part4Lint(unittest.TestCase):
    def test_flags_pr_totals(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(FIXTURES, "pr_totals.py")) as src, open(os.path.join(tmp, "totals.py"), "w") as dst:
                dst.write(src.read())
            r = lint(tmp)
        self.assertEqual(r.returncode, 1)
        self.assertIn("totals.py:", r.stdout)

    def test_each_kind(self):
        self.assertEqual(lint_source("x = float('1.5')\n").returncode, 1)
        self.assertEqual(lint_source("x = round(7 / 2)\n").returncode, 1)
        self.assertEqual(lint_source("x = 2 * 0.5\n").returncode, 1)

    def test_reports_line(self):
        r = lint_source("a = 1\nb = 2\nc = 0.5\n")
        self.assertIn(":3", r.stdout)

    def test_clean_code(self):
        self.assertEqual(lint_source("x = 7 // 2\ns = 'float(1.5)'\n").returncode, 0)

    def test_your_invoicing_is_clean(self):
        r = lint(os.path.join(os.getcwd(), "invoicing"))
        self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()
