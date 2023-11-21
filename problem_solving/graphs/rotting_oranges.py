"""
    https://leetcode.com/problems/rotting-oranges/
"""


import unittest
from typing import List


class Solution:
    def orangesRotting(self, grid: List[List[int]]) -> int:
        m, n = len(grid), len(grid[0])
        q = []
        for i, row in enumerate(grid):
            for j, val in enumerate(row):
                if val == 2:
                    q.append((i, j))
        nq = []
        mins = 0
        while q:
            x, y = q.pop()
            for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                if 0 <= x + dx < m and 0 <= y + dy < n and grid[x + dx][y + dy] == 1:
                    grid[x + dx][y + dy] = 2
                    nq.append((x + dx, y + dy))
            if not q and nq:
                mins += 1
                q, nq = nq, q

        for i, row in enumerate(grid):
            for j, val in enumerate(row):
                if val == 1:
                    return -1
        return mins


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(4, sol.orangesRotting([[2, 1, 1], [1, 1, 0], [0, 1, 1]]))
