import unittest

from radar.engine import evaluate, explain
from radar.models import Rule


def decide(txn, when):
    return evaluate(txn, [Rule("r", "block", when)])


class Part4(unittest.TestCase):
    def test_ordering_operators(self):
        txn = {"amount": 50000}
        self.assertEqual(decide(txn, "amount > 49999"), "block")
        self.assertEqual(decide(txn, "amount > 50000"), "accept")
        self.assertEqual(decide(txn, "amount >= 50000"), "block")
        self.assertEqual(decide(txn, "amount < 50001"), "block")
        self.assertEqual(decide(txn, "amount <= 49999"), "accept")
        self.assertEqual(decide(txn, "amount == 50000"), "block")
        self.assertEqual(decide(txn, "amount != 50000"), "accept")

    def test_literal_on_left(self):
        self.assertEqual(decide({"amount": 60000}, "50000 < amount"), "block")

    def test_negative_literal(self):
        self.assertEqual(decide({"amount": -5}, "amount < -1"), "block")

    def test_not_equal_strings(self):
        self.assertEqual(decide({"card_country": "US"}, 'card_country != "US"'), "accept")
        self.assertEqual(decide({"card_country": "GB"}, 'card_country != "US"'), "block")

    def test_field_to_field(self):
        when = "card_country != ip_country"
        self.assertEqual(decide({"card_country": "US", "ip_country": "NG"}, when), "block")
        self.assertEqual(decide({"card_country": "US", "ip_country": "US"}, when), "accept")

    def test_missing_field_is_false_even_for_not_equal(self):
        self.assertEqual(decide({}, 'card_country != "US"'), "accept")
        self.assertEqual(decide({"card_country": "US"}, "card_country != ip_country"), "accept")

    def test_mixed_types_are_false(self):
        self.assertEqual(decide({"amount": 1}, "amount == true"), "accept")
        self.assertEqual(decide({"amount": 0}, "amount == false"), "accept")
        self.assertEqual(decide({"is_3ds": True}, "is_3ds > 0"), "accept")
        self.assertEqual(decide({"is_3ds": True}, "is_3ds == 1"), "accept")
        self.assertEqual(decide({"amount": 5}, 'amount == "5"'), "accept")
        self.assertEqual(decide({"amount": 5}, 'amount != "5"'), "accept")
        self.assertEqual(decide({"merchant_name": "b"}, 'merchant_name > "a"'), "accept")

    def test_operators_combine_with_part3(self):
        when = '(amount > 100000 OR card_country != ip_country) AND is_3ds == false'
        self.assertEqual(decide({"amount": 5, "card_country": "US", "ip_country": "NG", "is_3ds": False}, when), "block")

    def test_review_action(self):
        rules = [Rule("rv", "review", "amount > 1000"), Rule("bl", "block", "amount > 0")]
        self.assertEqual(evaluate({"amount": 5000}, rules), "review")

    def test_explain(self):
        rules = [Rule("small", "accept", "amount < 100"), Rule("big", "block", "amount >= 100")]
        d = explain({"amount": 500}, rules)
        self.assertEqual((d.action, d.rule_id), ("block", "big"))
        d = explain({"amount": 5}, rules)
        self.assertEqual((d.action, d.rule_id), ("accept", "small"))

    def test_explain_default(self):
        d = explain({"amount": 5}, [Rule("big", "block", "amount > 100")])
        self.assertEqual(d.action, "accept")
        self.assertIsNone(d.rule_id)


if __name__ == "__main__":
    unittest.main()
