import unittest

from radar.engine import evaluate
from radar.models import Rule


def decide(txn, when):
    return evaluate(txn, [Rule("r", "block", when)])


class Part2(unittest.TestCase):
    def test_or(self):
        when = 'merchant_name == "Evil Corp" OR card_country == "NG"'
        self.assertEqual(decide({"merchant_name": "x", "card_country": "NG"}, when), "block")
        self.assertEqual(decide({"merchant_name": "Evil Corp", "card_country": "US"}, when), "block")
        self.assertEqual(decide({"merchant_name": "x", "card_country": "US"}, when), "accept")

    def test_and_with_boolean(self):
        when = 'is_3ds == false AND card_country == "BR"'
        self.assertEqual(decide({"is_3ds": False, "card_country": "BR"}, when), "block")
        self.assertEqual(decide({"is_3ds": True, "card_country": "BR"}, when), "accept")

    def test_boolean_literal_on_left(self):
        self.assertEqual(decide({"is_3ds": True}, "true == is_3ds"), "block")

    def test_quoted_true_is_a_string(self):
        self.assertEqual(decide({"is_3ds": True}, 'is_3ds == "true"'), "accept")
        self.assertEqual(decide({"is_3ds": "true"}, 'is_3ds == "true"'), "block")
        self.assertEqual(decide({"is_3ds": "true"}, "is_3ds == true"), "accept")

    def test_keywords_inside_quotes_are_text(self):
        self.assertEqual(decide({"merchant_name": "Bread and Butter"}, 'merchant_name == "Bread and Butter"'), "block")
        self.assertEqual(decide({"merchant_name": "Salt OR Pepper"}, 'merchant_name == "Salt OR Pepper"'), "block")
        self.assertEqual(decide({"merchant_name": "Bread"}, 'merchant_name == "Bread and Butter"'), "accept")

    def test_keyword_inside_quotes_with_real_keyword(self):
        when = 'merchant_name == "Rock and Roll" AND card_country == "US"'
        self.assertEqual(decide({"merchant_name": "Rock and Roll", "card_country": "US"}, when), "block")
        self.assertEqual(decide({"merchant_name": "Rock and Roll", "card_country": "GB"}, when), "accept")

    def test_keywords_any_case(self):
        when = 'merchant_name == "a" or merchant_name == "b" And card_country == "US"'
        self.assertEqual(decide({"merchant_name": "b", "card_country": "US"}, when), "block")

    def test_left_to_right_no_precedence(self):
        # (a OR b) AND c, not a OR (b AND c)
        when = 'merchant_name == "a" OR merchant_name == "b" AND card_country == "US"'
        self.assertEqual(decide({"merchant_name": "a", "card_country": "GB"}, when), "accept")
        self.assertEqual(decide({"merchant_name": "a", "card_country": "US"}, when), "block")

    def test_left_to_right_and_then_or(self):
        # (a AND b) OR c
        when = 'merchant_name == "a" AND card_country == "US" OR is_3ds == false'
        self.assertEqual(decide({"merchant_name": "z", "card_country": "GB", "is_3ds": False}, when), "block")

    def test_missing_field_in_compound(self):
        when = 'merchant_name == "a" OR card_country == "NG"'
        self.assertEqual(decide({"card_country": "NG"}, when), "block")
        self.assertEqual(decide({}, when), "accept")


if __name__ == "__main__":
    unittest.main()
