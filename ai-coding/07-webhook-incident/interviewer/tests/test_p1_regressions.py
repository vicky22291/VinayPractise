"""Part 1: each planted root cause must be caught by at least one of the candidate's own tests.

Method: run the candidate's tests/ against the answer-key package (baseline), then against the
answer-key package with one root cause put back (mutant). A root cause counts as caught when some
test passes on the baseline and fails on that mutant. Tests that fail on the baseline are ignored.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
RUN = Path.cwd()
MUTANTS = {
    "signature over re-encoded JSON": (
        "hooks/dispatcher.py",
        "signing.sign(body, endpoint.secret, now)",
        "signing.sign(__import__('json').dumps(envelope, separators=(',', ':')).encode('utf-8'), endpoint.secret, now)",
    ),
    "id changes on every attempt": (
        "hooks/serializer.py",
        '"id": event.id,',
        '"id": __import__("uuid").uuid4().hex,',
    ),
    "max_age in minutes": (
        "hooks/retry.py",
        "max_age: int = 3 * 24 * 60 * 60",
        "max_age: int = 3 * 24 * 60",
    ),
}
RUNNER = r"""
import json, unittest
def ids(suite):
    for t in suite:
        if isinstance(t, unittest.TestSuite):
            yield from ids(t)
        else:
            yield t.id()
suite = unittest.defaultTestLoader.discover("tests", top_level_dir=".")
every = list(ids(suite))  # before run(): a suite drops its tests as it runs them
result = unittest.TestResult()
suite.run(result)
print(json.dumps({"all": every, "bad": [t.id() for t, _ in result.failures + result.errors]}))
"""


def build(tmp, mutant):
    root = Path(tmp) / (mutant or "baseline").replace(" ", "_")
    for pkg in ("hooks", "sdk"):
        shutil.copytree(KIT / "candidate" / pkg, root / pkg)
        if (KIT / "interviewer" / "solution" / pkg).is_dir():
            shutil.copytree(KIT / "interviewer" / "solution" / pkg, root / pkg, dirs_exist_ok=True)
    shutil.copytree(RUN / "tests", root / "tests", ignore=shutil.ignore_patterns("__pycache__"))
    if mutant:
        rel, old, new = MUTANTS[mutant]
        path = root / rel
        text = path.read_text()
        if old not in text:
            raise RuntimeError(f"kit maintenance: {old!r} not found in answer key {rel}")
        path.write_text(text.replace(old, new))
    return root


def run_suite(root):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run([sys.executable, "-c", RUNNER], cwd=root, env=env, capture_output=True, text=True, timeout=120)
    if p.returncode != 0 or not p.stdout.strip():
        raise RuntimeError("could not run tests/:\n" + p.stderr[-2000:])
    return json.loads(p.stdout.strip().splitlines()[-1])


class Part1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        base = run_suite(build(cls.tmp, None))
        cls.good = set(base["all"]) - set(base["bad"])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def assert_caught(self, mutant):
        res = run_suite(build(self.tmp, mutant))
        caught = sorted(self.good & set(res["bad"]))
        self.assertTrue(caught, f"no test in tests/ catches: {mutant}")

    def test_catches_signature_root_cause(self):
        self.assert_caught("signature over re-encoded JSON")

    def test_catches_event_id_root_cause(self):
        self.assert_caught("id changes on every attempt")

    def test_catches_give_up_root_cause(self):
        self.assert_caught("max_age in minutes")


if __name__ == "__main__":
    unittest.main()
