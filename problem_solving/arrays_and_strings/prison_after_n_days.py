"""
    https://leetcode.com/problems/prison-cells-after-n-days/
"""
import unittest
from typing import List


class Solution:
    def prisonAfterNDays(self, cells: List[int], n: int) -> List[int]:
        k = len(cells)
        days = []

        def getNext(row):
            nonlocal k

            ans = [0]
            for i in range(1, k - 1):
                if row[i - 1] == row[i + 1]:
                    ans.append(1)
                else:
                    ans.append(0)
            ans.append(0)
            return tuple(ans)

        prev = cells
        for i in range(14):
            nextCells = getNext(prev)
            days.append(nextCells)
            prev = nextCells

        return list(days[(n - 1) % 14])


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual([0, 0, 1, 1, 0, 0, 0, 0], sol.prisonAfterNDays([0, 1, 0, 1, 1, 0, 0, 1], 7))

    def testSample2(self):
        sol = Solution()
        self.assertEqual([0, 0, 1, 1, 1, 1, 1, 0], sol.prisonAfterNDays([1, 0, 0, 1, 0, 0, 1, 0], 1000000000))
