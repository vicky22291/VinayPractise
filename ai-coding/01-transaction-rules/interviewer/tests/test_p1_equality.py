import unittest

from radar.engine import evaluate
from radar.models import Rule


def block(when, rid="r"):
    return Rule(rid, "block", when)


class Part1(unittest.TestCase):
    def test_field_on_left(self):
        self.assertEqual(evaluate({"merchant_name": "Evil Corp"}, [block('merchant_name == "Evil Corp"')]), "block")

    def test_value_on_left_risk_101(self):
        self.assertEqual(evaluate({"merchant_name": "Evil Corp"}, [block('"Evil Corp" == merchant_name')]), "block")
        self.assertEqual(evaluate({"merchant_name": "Good"}, [block('"Evil Corp" == merchant_name')]), "accept")

    def test_exact_match_not_substring_risk_102(self):
        rules = [block('merchant_name == "Bad LLC"')]
        self.assertEqual(evaluate({"merchant_name": "Not Bad LLC"}, rules), "accept")
        self.assertEqual(evaluate({"merchant_name": "Bad LLC"}, rules), "block")
        self.assertEqual(evaluate({"merchant_name": "Bad"}, rules), "accept")

    def test_operator_inside_value(self):
        rules = [block('merchant_name == "A == B Ltd"')]
        self.assertEqual(evaluate({"merchant_name": "A == B Ltd"}, rules), "block")

    def test_first_match_in_list_order_wins_risk_103(self):
        rules = [
            Rule("allow", "accept", 'merchant_name == "Fresh Mart"'),
            block('merchant_name == "Evil Corp"', "evil"),
            block('card_country == "BR"', "br"),
        ]
        self.assertEqual(evaluate({"merchant_name": "Fresh Mart", "card_country": "BR"}, rules), "accept")
        self.assertEqual(evaluate({"merchant_name": "Other", "card_country": "BR"}, rules), "block")

    def test_non_string_field_does_not_match_string(self):
        self.assertEqual(evaluate({"amount": 5}, [block('amount == "5"')]), "accept")

    def test_missing_field_does_not_match_risk_104(self):
        rules = [block('merchant_name == "Evil Corp"'), block('card_country == "NG"', "ng")]
        self.assertEqual(evaluate({"card_country": "US"}, rules), "accept")
        self.assertEqual(evaluate({"card_country": "NG"}, rules), "block")

    def test_whitespace_optional(self):
        self.assertEqual(evaluate({"merchant_name": "Evil Corp"}, [block('merchant_name=="Evil Corp"')]), "block")
        self.assertEqual(evaluate({"merchant_name": "Evil Corp"}, [block('  merchant_name   ==   "Evil Corp"  ')]), "block")

    def test_spaces_inside_quotes_are_kept(self):
        rules = [block('merchant_name == "Evil  Corp"')]
        self.assertEqual(evaluate({"merchant_name": "Evil Corp"}, rules), "accept")
        self.assertEqual(evaluate({"merchant_name": "Evil  Corp"}, rules), "block")

    def test_case_sensitive(self):
        self.assertEqual(evaluate({"merchant_name": "evil corp"}, [block('merchant_name == "Evil Corp"')]), "accept")

    def test_empty_string_value(self):
        self.assertEqual(evaluate({"merchant_name": ""}, [block('merchant_name == ""')]), "block")

    def test_default_accept(self):
        self.assertEqual(evaluate({"merchant_name": "x"}, []), "accept")


if __name__ == "__main__":
    unittest.main()
