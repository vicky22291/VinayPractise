import unittest

from radar.engine import evaluate
from radar.errors import RuleSyntaxError
from radar.models import Rule


def decide(txn, when):
    return evaluate(txn, [Rule("r", "block", when)])


class Part3(unittest.TestCase):
    def test_group_then_and(self):
        when = '(merchant_name == "Evil Corp" OR merchant_name == "Bad LLC") AND card_country == "NG"'
        self.assertEqual(decide({"merchant_name": "Bad LLC", "card_country": "NG"}, when), "block")
        self.assertEqual(decide({"merchant_name": "Bad LLC", "card_country": "US"}, when), "accept")

    def test_group_overrides_left_to_right(self):
        when = 'merchant_name == "a" OR (merchant_name == "b" AND card_country == "US")'
        self.assertEqual(decide({"merchant_name": "a", "card_country": "GB"}, when), "block")

    def test_nested(self):
        when = 'is_3ds == false AND ((card_country == "BR") OR (ip_country == "BR"))'
        self.assertEqual(decide({"is_3ds": False, "card_country": "US", "ip_country": "BR"}, when), "block")
        self.assertEqual(decide({"is_3ds": False, "card_country": "US", "ip_country": "US"}, when), "accept")
        self.assertEqual(decide({"is_3ds": True, "card_country": "BR", "ip_country": "BR"}, when), "accept")

    def test_deep_nesting(self):
        when = "(((((" + 'merchant_name == "x"' + ")))))"
        self.assertEqual(decide({"merchant_name": "x"}, when), "block")

    def test_parens_inside_quotes_are_text(self):
        self.assertEqual(decide({"merchant_name": "Shop (UK)"}, 'merchant_name == "Shop (UK)"'), "block")

    def test_bad_rules_raise_with_id(self):
        bad = [
            '(merchant_name == "x"',
            'merchant_name == "x")',
            "()",
            "merchant_name ==",
            'merchant_name == "x',
            'merchant_name ~ "x"',
            'merchant_name = "x"',
            'merchant_name == "x" AND',
            'merchant_name == "x" card_country == "US"',
            "",
        ]
        for when in bad:
            with self.subTest(when=when):
                with self.assertRaises(RuleSyntaxError) as ctx:
                    evaluate({"merchant_name": "x"}, [Rule("bad-rule-7", "block", when)])
                self.assertIn("bad-rule-7", str(ctx.exception))

    def test_bad_rule_later_in_list_still_raises(self):
        rules = [Rule("good", "block", 'merchant_name == "x"'), Rule("broken", "block", '(card_country == "US"')]
        with self.assertRaises(RuleSyntaxError) as ctx:
            evaluate({"merchant_name": "x"}, rules)
        self.assertIn("broken", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
