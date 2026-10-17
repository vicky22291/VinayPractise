import unittest

from kyc import validate_csv
from tests.helpers import HEADER, ROW_1, ROW_2, codes


class ValidateCsvTest(unittest.TestCase):
    def test_valid_file(self):
        results = validate_csv("\n".join([HEADER, ROW_1, ROW_2]))
        self.assertEqual([r.record_id for r in results], ["m-1", "m-2"])
        self.assertEqual([r.line for r in results], [2, 3])
        self.assertTrue(all(r.valid for r in results))

    def test_wrong_column_count(self):
        results = validate_csv("\n".join([HEADER, "m-9,Short Row,12-3456789"]))
        self.assertEqual(codes(results[0]), [("WRONG_COLUMN_COUNT", "*")])
        self.assertEqual(results[0].record_id, "m-9")

    def test_crlf_line_endings(self):
        results = validate_csv("\r\n".join([HEADER, ROW_1, ROW_2]))
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.valid for r in results), [r.errors for r in results])

    def test_trailing_newline_is_not_a_record(self):
        results = validate_csv("\n".join([HEADER, ROW_1]) + "\n")
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].valid)


if __name__ == "__main__":
    unittest.main()
