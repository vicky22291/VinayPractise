"""Part 1: do the candidate's characterization tests notice small changes?

Each file in mutants/ is the legacy billing/invoice.py with one small,
realistic change. For each one: copy the run dir, swap in the mutant, run the
candidate's suite. A failing suite kills the mutant. Pass mark: 75% killed.
Survivors are listed by id only; answer-key.md says what each one changes.
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
MUTANTS = sorted(glob.glob(os.path.join(HERE, "mutants", "m*.py")))
PASS_MARK = 0.75
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def run_suite(root):
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."]
    return subprocess.run(cmd, cwd=root, env=ENV, capture_output=True, text=True, timeout=300)


class Part1Mutants(unittest.TestCase):
    def test_suite_is_green_on_current_code(self):
        r = run_suite(os.getcwd())
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, 0, "your suite must pass on the current code:\n" + out[-1500:])
        self.assertNotIn("Ran 0 tests", out, "no tests found under tests/")

    def test_kills_mutants(self):
        baseline = run_suite(os.getcwd())
        if baseline.returncode != 0 or "Ran 0 tests" in baseline.stdout + baseline.stderr:
            self.fail("kill rate not measured: your suite must run and pass on the current code first")
        survivors = []
        for path in MUTANTS:
            with tempfile.TemporaryDirectory() as tmp:
                root = os.path.join(tmp, "run")
                shutil.copytree(os.getcwd(), root, ignore=shutil.ignore_patterns(".git", "__pycache__"))
                shutil.copy(path, os.path.join(root, "billing", "invoice.py"))
                if run_suite(root).returncode == 0:
                    survivors.append(os.path.basename(path)[:-3])
        killed = len(MUTANTS) - len(survivors)
        self.assertGreaterEqual(
            killed / len(MUTANTS), PASS_MARK,
            f"killed {killed} of {len(MUTANTS)}; survivors: {', '.join(survivors)}",
        )


if __name__ == "__main__":
    unittest.main()
