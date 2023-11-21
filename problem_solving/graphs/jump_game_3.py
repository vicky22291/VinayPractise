import unittest
from typing import List


"""
    Problem: https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/707/traversals-trees-graphs/4672/
"""


class Solution:
    def canReach(self, arr: List[int], start: int) -> bool:
        if arr[start] == 0:
            return True
        n = len(arr)
        curQ = [start]
        seen = {start}
        nxtQ = []
        while curQ:
            index = curQ.pop()
            for i in [index + arr[index], index - arr[index]]:
                if i < n and arr[i] == 0:
                    return True
                if i not in seen and 0 <= i < n:
                    nxtQ.append(i)
                    seen.add(i)
            if not curQ:
                curQ, nxtQ = nxtQ, curQ
        return False


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertTrue(sol.canReach([4, 2, 3, 0, 3, 1, 2], 5))

    def testSample2(self):
        sol = Solution()
        self.assertTrue(sol.canReach([4, 2, 3, 0, 3, 1, 2], 0))

    def testSample3(self):
        sol = Solution()
        self.assertFalse(sol.canReach([3, 0, 2, 1, 2], 2))
