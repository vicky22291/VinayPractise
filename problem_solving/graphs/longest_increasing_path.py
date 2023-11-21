"""
    https://leetcode.com/problems/longest-increasing-path-in-a-matrix/submissions/
"""
from typing import List


class Solution:
    def longestIncreasingPath(self, grid: List[List[int]]) -> int:
        row, col, ans = len(grid), len(grid[0]), 0
        memo = {}

        def Path(i, j):
            if (i, j) in memo:
                return memo[(i, j)]

            res = 0
            if i + 1 < row and grid[i][j] < grid[i + 1][j]:
                res = max(res, 1 + Path(i + 1, j))

            if i - 1 >= 0 and grid[i][j] < grid[i - 1][j]:
                res = max(res, 1 + Path(i - 1, j))

            if j + 1 < col and grid[i][j] < grid[i][j + 1]:
                res = max(res, 1 + Path(i, j + 1))

            if j - 1 >= 0 and grid[i][j] < grid[i][j - 1]:
                res = max(res, 1 + Path(i, j - 1))

            memo[(i, j)] = res
            return memo[(i, j)]

        for i in range(row):
            for j in range(col):
                ans = max(ans, Path(i, j))

        return ans + 1