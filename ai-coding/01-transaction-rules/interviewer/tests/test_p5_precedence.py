import itertools
import unittest

from radar.engine import evaluate, migrate
from radar.models import Rule

A_OR_B_AND_C = "a == true OR b == true AND c == true"


def txns():
    for a, b, c, d in itertools.product([True, False], repeat=4):
        yield {"a": a, "b": b, "c": c, "d": d}


class Part5(unittest.TestCase):
    def test_version_defaults_to_1(self):
        self.assertEqual(Rule("r", "block", A_OR_B_AND_C).version, 1)

    def test_v1_left_to_right(self):
        rule = Rule("r", "block", A_OR_B_AND_C)
        self.assertEqual(evaluate({"a": True, "b": False, "c": False}, [rule]), "accept")

    def test_v2_and_binds_tighter(self):
        rule = Rule("r", "block", A_OR_B_AND_C, version=2)
        self.assertEqual(evaluate({"a": True, "b": False, "c": False}, [rule]), "block")
        self.assertEqual(evaluate({"a": False, "b": True, "c": False}, [rule]), "accept")

    def test_v2_parentheses_override(self):
        rule = Rule("r", "block", "(a == true OR b == true) AND c == true", version=2)
        self.assertEqual(evaluate({"a": True, "b": False, "c": False}, [rule]), "accept")

    def test_v2_and_or_and(self):
        rule = Rule("r", "block", "a == true AND b == true OR c == true AND d == true", version=2)
        self.assertEqual(evaluate({"a": False, "b": False, "c": True, "d": True}, [rule]), "block")

    def test_migrate_keeps_every_decision(self):
        clauses = [
            A_OR_B_AND_C,
            "a == true AND b == true OR c == true AND d == true",
            "a == true OR b == true OR c == true AND d == false",
            "(a == true OR b == true) AND c == true OR d == true",
            "a == true OR (b == true AND c == false OR d == true) AND a == false",
            "a == true",
        ]
        for when in clauses:
            old = Rule("id-1", "review", when)
            new = migrate(old)
            with self.subTest(when=when, migrated=new.when):
                self.assertEqual(new.version, 2)
                self.assertEqual((new.id, new.action), ("id-1", "review"))
                for txn in txns():
                    self.assertEqual(evaluate(txn, [old]), evaluate(txn, [new]))

    def test_migrate_v2_unchanged(self):
        rule = Rule("r", "block", A_OR_B_AND_C, version=2)
        self.assertEqual(migrate(rule), rule)

    def test_migrate_twice_is_stable(self):
        once = migrate(Rule("r", "block", A_OR_B_AND_C))
        self.assertEqual(migrate(once), once)


if __name__ == "__main__":
    unittest.main()
