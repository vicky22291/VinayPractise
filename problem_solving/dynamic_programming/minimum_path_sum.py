import math
import unittest
from functools import cache
from typing import List

"""
    https://leetcode.com/explore/learn/card/dynamic-programming/634/matrix-path-based-dp/4132/
"""


class Solution:
    def minPathSum(self, grid: List[List[int]]) -> int:
        m, n = len(grid), len(grid[0])

        @cache
        def dp(i, j):
            if i + j == 0:
                return grid[i][j]

            minSum = math.inf

            if i > 0:
                minSum = min(minSum, dp(i - 1, j) + grid[i][j])
            if j > 0:
                minSum = min(minSum, dp(i, j - 1) + grid[i][j])
            return minSum

        return dp(m - 1, n - 1)


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(7, sol.minPathSum([[1, 3, 1], [1, 5, 1], [4, 2, 1]]))
