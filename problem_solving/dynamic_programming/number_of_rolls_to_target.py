"""
    https://leetcode.com/problems/number-of-dice-rolls-with-target-sum/
"""
import unittest
from functools import cache


class Solution:
    def numRollsToTarget(self, n: int, k: int, target: int) -> int:
        @cache
        def backtracking(i, t):
            nonlocal k

            if i == 0 and t == 0:
                return 1
            if i == 0 or t == 0:
                return 0
            ways = 0
            for j in range(min(t, k) - 1, -1, -1):
                ways += backtracking(i - 1, t - j - 1)
            return ways

        return backtracking(n, target) % (10 ** 9 + 7)


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(1, sol.numRollsToTarget(1, 6, 3))
        self.assertEqual(6, sol.numRollsToTarget(2, 6, 7))

    def testSample2(self):
        sol = Solution()
        self.assertEqual(222616187, sol.numRollsToTarget(30, 30, 500))