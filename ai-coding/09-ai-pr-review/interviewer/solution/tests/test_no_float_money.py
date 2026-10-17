import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class LintTest(unittest.TestCase):
    def test_invoicing_has_no_float_money(self):
        tool = os.path.join(ROOT, "tools", "no_float_money.py")
        r = subprocess.run([sys.executable, tool, os.path.join(ROOT, "invoicing")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()
