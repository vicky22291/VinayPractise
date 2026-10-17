import json
import unittest

from kyc.models import RecordResult, ValidationError
from kyc.report import format_report, to_error_csv, to_json


class ReportTest(unittest.TestCase):
    def test_report_lists_each_error(self):
        results = [
            RecordResult(2, "m-1", []),
            RecordResult(3, "m-2", [ValidationError("INVALID_EMAIL", "owner_email", "bad email 'x'")]),
        ]
        text = format_report(results)
        self.assertIn("2 records: 1 valid, 1 invalid", text)
        self.assertIn("line 3 (m-2): INVALID_EMAIL owner_email", text)

    def test_json_lists_only_invalid_records(self):
        results = [
            RecordResult(2, "m-1", []),
            RecordResult(3, "m-2", [ValidationError("INVALID_EMAIL", "owner_email", "bad email 'x'")]),
        ]
        doc = json.loads(to_json(results))
        self.assertEqual((doc["total"], doc["valid"], doc["invalid"]), (2, 1, 1))
        self.assertEqual([r["record_id"] for r in doc["records"]], ["m-2"])

    def test_error_csv_most_urgent_first(self):
        results = [
            RecordResult(2, "m-1", [ValidationError("INVALID_EMAIL", "owner_email", "bad, very bad")]),
            RecordResult(3, "m-2", [ValidationError("MISSING_FIELD", "tax_id", "tax_id is required")]),
        ]
        lines = to_error_csv(results).splitlines()
        self.assertEqual(lines[1], "1,3,m-2,MISSING_FIELD,tax_id,tax_id is required")
        self.assertEqual(lines[2], '3,2,m-1,INVALID_EMAIL,owner_email,"bad, very bad"')


if __name__ == "__main__":
    unittest.main()
