import unittest

from kyc import ValidationError, validate_csv
from kyc.rules import DEFAULT_RULES
from kyc_fixtures import HEADER, US, codes, row


def check(**fields):
    return codes(validate_csv(HEADER + "\n" + row(**fields))[0])


class AlwaysFlag:
    def check(self, record):
        return [ValidationError("FLAGGED", "record_id", "flagged " + record["record_id"])]


class Part2Rules(unittest.TestCase):
    def test_custom_rule_added(self):
        results = validate_csv(HEADER + "\n" + row(name=""), rules=list(DEFAULT_RULES) + [AlwaysFlag()])
        self.assertEqual(codes(results[0]), [("FLAGGED", "record_id"), ("MISSING_FIELD", "business_name")])

    def test_rules_list_replaces_defaults(self):
        results = validate_csv(HEADER + "\n" + row(name="", email="nope"), rules=[AlwaysFlag()])
        self.assertEqual(codes(results[0]), [("FLAGGED", "record_id")])

    def test_empty_rules_still_checks_column_count(self):
        results = validate_csv("\n".join([HEADER, "m-7,Short", US]), rules=[])
        self.assertEqual(codes(results[0]), [("WRONG_COLUMN_COUNT", "*")])
        self.assertTrue(results[1].valid)

    def test_record_is_lowercase_keys_trimmed_values(self):
        seen = []

        class Spy:
            def check(self, record):
                seen.append(record)
                return []

        header = HEADER.replace("record_id", " Record_ID ")
        validate_csv(header + "\n" + row(record_id=" m-5 "), rules=[Spy()])
        self.assertEqual(seen[0]["record_id"], "m-5")

    def test_forbidden_words(self):
        for name, ok in {
            "Blood Bank Cafe": False,
            "TEST Shop": False,
            "Totally Fake Goods": False,
            "fake": False,
            "Bankside Cafe": True,
            "Contest Supplies": True,
            "Testa Rossa": True,
        }.items():
            with self.subTest(name=name):
                expected = [] if ok else [("FORBIDDEN_WORD", "business_name")]
                self.assertEqual(check(name=name), expected)

    def test_tax_id_per_country(self):
        cases = [
            ("US", "12-3456789", True),
            ("US", "123456789", False),
            ("US", "12-345678", False),
            ("GB", "09887766", True),
            ("GB", "SC123456", True),
            ("GB", "sc123456", False),
            ("GB", "0988776", False),
            ("CA", "123456789", True),
            ("CA", "12345678A", False),
            ("FR", "FR12345678", True),
            ("FR", "FR 1234", False),
        ]
        for country, tax_id, ok in cases:
            with self.subTest(country=country, tax_id=tax_id):
                expected = [] if ok else [("INVALID_TAX_ID", "tax_id")]
                self.assertEqual(check(country=country, tax_id=tax_id), expected)

    def test_too_long(self):
        self.assertEqual(check(name="A" * 80), [])
        self.assertEqual(check(name="A" * 81), [("TOO_LONG", "business_name")])
        self.assertEqual(check(owner="é" * 60), [])
        self.assertEqual(check(owner="é" * 61), [("TOO_LONG", "owner_name")])

    def test_part1_checks_are_default_rules(self):
        self.assertEqual(check(country="ZZ"), [("INVALID_COUNTRY", "country")])
        self.assertEqual(check(name="", owner=""), [("MISSING_FIELD", "business_name"), ("MISSING_FIELD", "owner_name")])


if __name__ == "__main__":
    unittest.main()
