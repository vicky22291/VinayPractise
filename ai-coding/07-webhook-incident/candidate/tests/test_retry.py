import unittest

from hooks.retry import RetryPolicy


class RetryPolicyTest(unittest.TestCase):
    def test_first_retry_after_two_minutes(self):
        self.assertEqual(RetryPolicy().next_attempt_at(created_at=0, attempts=1, now=0), 120)

    def test_backoff_doubles(self):
        p = RetryPolicy()
        self.assertEqual(p.next_attempt_at(0, 2, 120), 120 + 240)
        self.assertEqual(p.next_attempt_at(0, 3, 360), 360 + 480)


if __name__ == "__main__":
    unittest.main()
