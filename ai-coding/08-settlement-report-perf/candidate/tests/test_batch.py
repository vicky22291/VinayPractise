import unittest

from payouts.batch import Instruction, instructions

REPORT = """merchant_id,merchant_name,currency,count,charges,refunds,disputes,fees,net,payout_currency,payout_amount
acct_1,Smith, Jones & Co,eur,1,1000,0,0,59,941,usd,1020
acct_1,Smith, Jones & Co,usd,2,5000,0,0,205,4795,usd,4795
acct_2,Tiny,usd,1,100,0,0,33,67,usd,67
acct_3,Refundy,usd,1,0,900,0,0,-900,usd,-900
TOTAL,,,,,,,,,usd,4982
"""


class BatchTest(unittest.TestCase):
    def test_sums_lines_per_merchant(self):
        pay, carry = instructions(REPORT)
        self.assertEqual(pay, [Instruction("acct_1", "usd", 5815)])
        self.assertEqual(carry, {("acct_2", "usd"): 67, ("acct_3", "usd"): -900})

    def test_carried_amounts_are_added(self):
        pay, carry = instructions(REPORT, carried={("acct_2", "usd"): 40})
        self.assertIn(Instruction("acct_2", "usd", 107), pay)


if __name__ == "__main__":
    unittest.main()
