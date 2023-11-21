"""
    https://leetcode.com/problems/rank-transform-of-an-array/
"""


import unittest
from typing import List


class Solution:
    def arrayRankTransform(self, arr: List[int]) -> List[int]:
        data = {i: num for i, num in enumerate(arr)}
        rankedList = sorted(data.items(), key=lambda x: x[1])
        ranks = [0] * len(arr)
        rank = 1
        prev = None
        for i, num in rankedList:
            if prev == num:
                ranks[i] = rank - 1
            else:
                ranks[i] = rank
                rank += 1
            prev = num
        return ranks


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual([4, 1, 2, 3], sol.arrayRankTransform([40, 10, 20, 30]))

    def testSample2(self):
        sol = Solution()
        self.assertEqual([1, 1, 1], sol.arrayRankTransform([100, 100, 100]))
