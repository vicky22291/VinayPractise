import unittest
from decimal import Decimal

from payouts.models import BalanceTransaction as T
from payouts.models import FxRate, Merchant
from payouts.report import HEADER, build_report
from payouts.store import Store

DAY = "2026-10-14"
RATES = [FxRate(DAY, "eur", "usd", Decimal("1.084100")), FxRate(DAY, "usd", "eur", Decimal("0.922424"))]


def report(merchants, txns):
    return build_report(Store(merchants, txns, RATES), DAY).splitlines()


class ReportTest(unittest.TestCase):
    def test_empty_day(self):
        self.assertEqual(report([Merchant("acct_1", "Acme", "usd")], []), [HEADER])

    def test_one_merchant_one_currency(self):
        lines = report([Merchant("acct_1", "Acme", "usd")], [
            T("t1", "acct_1", "charge", 10_000, 320, "usd", DAY),
            T("t2", "acct_1", "refund", -2_500, 0, "usd", DAY),
            T("t3", "acct_1", "dispute", -4_000, 1_500, "usd", DAY),
        ])
        self.assertEqual(lines[1:], [
            "acct_1,Acme,usd,3,10000,2500,4000,1820,1680,usd,1680",
            "TOTAL,,,,,,,,,usd,1680",
        ])

    def test_converts_to_payout_currency(self):
        lines = report([Merchant("acct_1", "Acme", "usd")], [T("t1", "acct_1", "charge", 10_000, 320, "eur", DAY)])
        self.assertEqual(lines[1], "acct_1,Acme,eur,1,10000,0,0,320,9680,usd,10494")

    def test_lines_sorted_by_merchant_then_currency(self):
        ms = [Merchant("acct_2", "Zed", "eur"), Merchant("acct_1", "Acme", "usd")]
        lines = report(ms, [
            T("t1", "acct_2", "charge", 1_000, 59, "usd", DAY),
            T("t2", "acct_1", "charge", 1_000, 59, "usd", DAY),
            T("t3", "acct_2", "charge", 1_000, 59, "eur", DAY),
        ])
        self.assertEqual([l.split(",")[0] + "/" + l.split(",")[2] for l in lines[1:4]],
                         ["acct_1/usd", "acct_2/eur", "acct_2/usd"])
        self.assertEqual(lines[4:], ["TOTAL,,,,,,,,,eur,1809", "TOTAL,,,,,,,,,usd,941"])

    def test_other_days_ignored(self):
        lines = report([Merchant("acct_1", "Acme", "usd")], [T("t1", "acct_1", "charge", 1_000, 59, "usd", "2026-10-13")])
        self.assertEqual(lines, [HEADER])


if __name__ == "__main__":
    unittest.main()
