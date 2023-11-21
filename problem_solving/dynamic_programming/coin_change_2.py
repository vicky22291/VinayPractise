import unittest
from functools import cache
from typing import List


"""
    https://leetcode.com/explore/learn/card/dynamic-programming/633/common-patterns-continued/4138/
"""


class Solution:
    def change(self, amount: int, coins: List[int]) -> int:
        @cache
        def dp(i, amt):
            if amt == 0:
                return 1
            elif i == len(coins):
                return 0

            if coins[i] > amt:
                return dp(i + 1, amt)
            else:
                return dp(i, amt - coins[i]) + dp(i + 1, amt)

        return dp(0, amount)


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(4, sol.change(5, [1, 2, 5]))
