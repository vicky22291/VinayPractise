import unittest

from kyc import validate_csv
from kyc_fixtures import HEADER, codes, row


def run(*rows, **kw):
    return validate_csv("\n".join([HEADER, *rows]), **kw)


class Part3Cross(unittest.TestCase):
    def test_duplicate_tax_id(self):
        results = run(
            row("a", tax_id="SC123456", country="GB", email="a@x.example"),
            row("b", name="Other Name", tax_id="sc123456", country="GB", email="b@x.example"),
            row("c", tax_id="SC123456", country="IE", email="c@x.example"),
        )
        self.assertEqual(codes(results[0]), [])
        self.assertEqual(codes(results[1]), [("DUPLICATE_TAX_ID", "tax_id"), ("INVALID_TAX_ID", "tax_id")])
        self.assertIn("line 2", [e for e in results[1].errors if e.code == "DUPLICATE_TAX_ID"][0].message)
        self.assertEqual(codes(results[2]), [], "same tax id in another country is a different business")

    def test_third_copy_points_at_first(self):
        results = run(
            row("a", email="a@x.example"),
            row("b", email="b@x.example"),
            row("c", email="c@x.example"),
        )
        dup = [e for e in results[2].errors if e.code == "DUPLICATE_TAX_ID"]
        self.assertEqual(len(dup), 1)
        self.assertIn("line 2", dup[0].message)

    def test_shared_owner(self):
        results = run(
            row("a", tax_id="11-1111111", email="Owner@Shell.example"),
            row("b", tax_id="22-2222222", email="owner@shell.example"),
            row("c", tax_id="11-1111111", email="owner@shell.example"),
        )
        self.assertEqual(codes(results[0]), [])
        self.assertEqual(codes(results[1]), [("SHARED_OWNER", "owner_email")])
        self.assertIn("line 2", results[1].errors[0].message)
        self.assertIn(("DUPLICATE_TAX_ID", "tax_id"), codes(results[2]))
        self.assertIn(("SHARED_OWNER", "owner_email"), codes(results[2]))

    def test_same_owner_same_tax_id_is_only_duplicate(self):
        results = run(row("a"), row("b"))
        self.assertEqual(codes(results[1]), [("DUPLICATE_TAX_ID", "tax_id")])

    def test_broken_rows_and_empty_values_ignored(self):
        results = run(
            "x,Short",
            row("a", tax_id="", email=""),
            row("b", tax_id="", email=""),
            row("c"),
        )
        self.assertEqual(codes(results[2]), [("MISSING_FIELD", "owner_email"), ("MISSING_FIELD", "tax_id")])
        self.assertEqual(codes(results[3]), [])

    def test_rules_argument_controls_cross_checks(self):
        results = run(row("a"), row("b"), rules=[])
        self.assertTrue(all(r.valid for r in results))

    def test_fresh_state_per_call(self):
        run(row("a"))
        self.assertEqual(codes(run(row("b"))[0]), [])


if __name__ == "__main__":
    unittest.main()
