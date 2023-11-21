import unittest
from functools import cache
from typing import List

"""
https://leetcode.com/explore/learn/card/dynamic-programming/632/common-patterns-in-dp-problems/4117/
"""


class Solution:
    def maxProfit(self, k: int, prices: List[int]) -> int:
        @cache
        def dp(i, k, hold):
            if i == len(prices) or (k == 0 and not hold):
                return 0
            if hold:
                return max(dp(i + 1, k, False) + prices[i], dp(i + 1, k, True))
            else:
                return max(dp(i + 1, k - 1, True) - prices[i], dp(i + 1, k, False))

        return dp(0, k, False)


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(7, sol.maxProfit(2, [3, 2, 6, 5, 0, 3]))
