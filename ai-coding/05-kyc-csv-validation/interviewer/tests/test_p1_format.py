import unittest

from kyc import HeaderError, validate_csv
from kyc_fixtures import CA, FR, GB, HEADER, US, codes, row


class Part1Format(unittest.TestCase):
    def test_plain_file(self):
        results = validate_csv("\n".join([HEADER, US, GB, CA, FR]))
        self.assertEqual([r.line for r in results], [2, 3, 4, 5])
        self.assertTrue(all(r.valid for r in results), [r.errors for r in results])

    def test_quoted_comma(self):
        results = validate_csv("\n".join([HEADER, row(name='"Acme, Inc."')]))
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].valid, results[0].errors)

    def test_escaped_quote_inside_quotes(self):
        results = validate_csv("\n".join([HEADER, row(name='"The ""Best"" Shop"')]))
        self.assertTrue(results[0].valid, results[0].errors)
        self.assertEqual(results[0].record_id, "m-9")

    def test_crlf_and_trailing_newline(self):
        results = validate_csv("\r\n".join([HEADER, US, GB]) + "\r\n")
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.valid for r in results), [r.errors for r in results])

    def test_trailing_newline_is_not_a_record(self):
        self.assertEqual(len(validate_csv(HEADER + "\n" + US + "\n")), 1)

    def test_blank_lines_skipped_and_counted(self):
        results = validate_csv("\n".join([HEADER, US, "", "   ", GB]))
        self.assertEqual([r.line for r in results], [2, 5])
        self.assertTrue(all(r.valid for r in results))

    def test_byte_order_mark(self):
        results = validate_csv("﻿" + "\n".join([HEADER, US]))
        self.assertEqual(results[0].record_id, "m-1")
        self.assertTrue(results[0].valid, results[0].errors)

    def test_header_case_spaces_and_order(self):
        header = " Owner_Email , RECORD_ID,business_name,Tax_Id,country,incorporation_date,owner_name,notes"
        line = "dana@bluebottle.example,m-1,Blue Bottle Roasters,12-3456789,US,2014-03-09,Dana Park,vip"
        results = validate_csv(header + "\n" + line)
        self.assertEqual(results[0].record_id, "m-1")
        self.assertTrue(results[0].valid, results[0].errors)

    def test_missing_column_raises(self):
        with self.assertRaises(HeaderError):
            validate_csv("record_id,business_name,tax_id,country\nm-1,Acme,12-3456789,US")

    def test_values_trimmed(self):
        line = "  m-1 , Blue Bottle Roasters ,12-3456789, US ,2014-03-09,Dana Park, dana@bluebottle.example "
        results = validate_csv(HEADER + "\n" + line)
        self.assertEqual(results[0].record_id, "m-1")
        self.assertTrue(results[0].valid, results[0].errors)

    def test_every_error_reported(self):
        line = row(name="", owner="", country="ZZ", date="2014-13-01", email="nope")
        self.assertEqual(
            codes(validate_csv(HEADER + "\n" + line)[0]),
            [
                ("INVALID_COUNTRY", "country"),
                ("INVALID_DATE", "incorporation_date"),
                ("INVALID_EMAIL", "owner_email"),
                ("MISSING_FIELD", "business_name"),
                ("MISSING_FIELD", "owner_name"),
            ],
        )

    def test_dates(self):
        cases = {
            "2023-02-30": False,
            "2023-04-31": False,
            "2023-02-29": False,
            "2024-02-29": True,
            "20230115": False,
            "2023-1-05": False,
            "2023-01-05": True,
        }
        for date, ok in cases.items():
            with self.subTest(date=date):
                result = validate_csv(HEADER + "\n" + row(date=date))[0]
                self.assertEqual(result.valid, ok, result.errors)

    def test_wrong_column_count_keeps_record_id(self):
        results = validate_csv("\n".join([HEADER, "m-7,Short Row,12-3456789", US]))
        self.assertEqual(codes(results[0]), [("WRONG_COLUMN_COUNT", "*")])
        self.assertEqual(results[0].record_id, "m-7")
        self.assertTrue(results[1].valid)


if __name__ == "__main__":
    unittest.main()
