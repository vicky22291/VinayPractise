import os
import tempfile
import unittest

from kyc.sources import latest_per_bank, list_drops


class SourcesTest(unittest.TestCase):
    def test_newest_file_per_bank(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ["a-20261001.csv", "a-20261003.csv", "b-20261002.csv", "notes.txt", "a-2026.csv"]:
                open(os.path.join(d, name), "w").close()
            latest = latest_per_bank(list_drops(d))
            self.assertEqual([(x.bank, x.day) for x in latest], [("a", "20261003"), ("b", "20261002")])


if __name__ == "__main__":
    unittest.main()
