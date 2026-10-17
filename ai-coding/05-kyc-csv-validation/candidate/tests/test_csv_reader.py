import unittest

from kyc.csv_reader import HeaderError, read_rows
from tests.helpers import HEADER, ROW_1


class ReadRowsTest(unittest.TestCase):
    def test_reads_header_and_rows(self):
        header, rows = read_rows(HEADER + "\n" + ROW_1)
        self.assertEqual(header[0], "record_id")
        self.assertEqual(rows[0][0], 2)
        self.assertEqual(rows[0][1][1], "Blue Bottle Roasters")

    def test_missing_column_raises(self):
        with self.assertRaises(HeaderError):
            read_rows("record_id,business_name\nm-1,Acme")

    def test_quoted_comma_stays_in_one_field(self):
        row = 'm-2,"Acme, Inc.",98-7654321,US,2009-11-30,Lee Wong,lee@acme.example'
        _, rows = read_rows(HEADER + "\n" + row)
        self.assertEqual(rows[0][1][1], "Acme, Inc.")
        self.assertEqual(len(rows[0][1]), 7)


if __name__ == "__main__":
    unittest.main()
