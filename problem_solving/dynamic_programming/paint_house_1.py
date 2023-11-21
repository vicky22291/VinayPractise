import math
import unittest
from functools import cache
from typing import List

"""
    https://leetcode.com/explore/learn/card/dynamic-programming/647/more-practice-problems/4074/
"""


class Solution:
    def minCost(self, costs: List[List[int]]) -> int:
        @cache
        def dp(i, c):
            minimum = math.inf
            for j in range(3):
                if j != c:
                    if i == 0:
                        minimum = min(minimum, costs[i][j])
                    else:
                        minimum = min(minimum, costs[i][j] + dp(i - 1, j))
            return minimum

        finalMin = math.inf
        for j in range(3):
            finalMin = min(finalMin, dp(len(costs) - 1, j))
        return finalMin


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(10, sol.minCost([[17, 2, 17], [16, 16, 5], [14, 3, 19]]))

    def testSample2(self):
        sol = Solution()
        self.assertEqual(2, sol.minCost([[7, 6, 2]]))
