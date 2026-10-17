import unittest

from kyc.validators import validate_record


def record(**overrides):
    base = {
        "record_id": "m-1",
        "business_name": "Blue Bottle Roasters",
        "tax_id": "12-3456789",
        "country": "US",
        "incorporation_date": "2014-03-09",
        "owner_name": "Dana Park",
        "owner_email": "dana@bluebottle.example",
    }
    base.update(overrides)
    return base


def codes(errors):
    return sorted((e.code, e.field) for e in errors)


class ValidateRecordTest(unittest.TestCase):
    def test_valid_record(self):
        self.assertEqual(validate_record(record()), [])

    def test_bad_email(self):
        self.assertEqual(codes(validate_record(record(owner_email="dana-at-example"))), [("INVALID_EMAIL", "owner_email")])

    def test_unknown_country(self):
        self.assertEqual(codes(validate_record(record(country="NZ"))), [("INVALID_COUNTRY", "country")])

    def test_every_missing_field_is_reported(self):
        errors = validate_record(record(business_name="", owner_name=""))
        self.assertEqual(codes(errors), [("MISSING_FIELD", "business_name"), ("MISSING_FIELD", "owner_name")])

    def test_impossible_date(self):
        self.assertEqual(
            codes(validate_record(record(incorporation_date="2023-02-30"))),
            [("INVALID_DATE", "incorporation_date")],
        )


if __name__ == "__main__":
    unittest.main()
