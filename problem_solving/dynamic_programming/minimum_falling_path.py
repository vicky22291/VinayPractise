import math
from functools import cache
from typing import List

"""
    https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/712/dynamic-programming/4586/
"""


class AlternativeSolution:
    def minFallingPathSum(self, matrix: List[List[int]]) -> int:
        m, n = len(matrix), len(matrix[0])

        @cache
        def dp(i, j):
            if i == 0:
                return matrix[i][j]
            minSum = dp(i - 1, j)

            if j > 0:
                minSum = min(minSum, dp(i - 1, j - 1))
            if j < n - 1:
                minSum = min(minSum, dp(i - 1, j + 1))
            return minSum + matrix[i][j]

        finalMin = math.inf
        for j in range(n):
            finalMin = min(finalMin, dp(m - 1, j))

        return finalMin


class Solution:
    def minFallingPathSum(self, matrix: List[List[int]]) -> int:
        m = len(matrix)
        for i in range(1, m):
            for j in range(m):
                matrix[i][j] += min(matrix[i - 1][k] for k in (j - 1, j, j + 1) if 0 <= k < m)
        return min(matrix[-1])
