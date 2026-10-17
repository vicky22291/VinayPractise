import unittest

from radar.engine import evaluate
from radar.models import Rule


class EvaluateTest(unittest.TestCase):
    def test_no_rules_accepts(self):
        self.assertEqual(evaluate({"merchant_name": "Shop"}, []), "accept")

    def test_matching_block_rule(self):
        rules = [Rule("r1", "block", 'merchant_name == "Evil Corp"')]
        self.assertEqual(evaluate({"merchant_name": "Evil Corp"}, rules), "block")

    def test_non_matching_rule_accepts(self):
        rules = [Rule("r1", "block", 'merchant_name == "Evil Corp"')]
        self.assertEqual(evaluate({"merchant_name": "Good Shop"}, rules), "accept")


if __name__ == "__main__":
    unittest.main()
