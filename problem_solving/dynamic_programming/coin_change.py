"""
    https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/712/dynamic-programming/4581/
"""
import unittest
from functools import cache
from typing import List
import math


class Solution:
    def coinChange(self, coins: List[int], amount: int) -> int:
        coins = sorted(coins)

        @cache
        def dp(n):
            if n == 0:
                return 0
            if n < coins[0]:
                return -1
            minValue = math.inf
            for coin in coins[::-1]:
                value = dp(n - coin)
                if value != -1:
                    minValue = min(minValue, value + 1)
            if minValue == math.inf:
                return -1
            return minValue

        return dp(amount)


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(3, sol.coinChange([1, 2, 5], 11))
