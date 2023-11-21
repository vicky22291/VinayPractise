import unittest
from typing import List


"""
    Problem: https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/707/traversals-trees-graphs/4693/
    using a Simple BFS
"""


class Solution:
    def validPath(self, n: int, edges: List[List[int]], source: int, destination: int) -> bool:
        if source == destination:
            return True
        adjacencies = [[] for _ in range(n)]
        for x, y in edges:
            adjacencies[x].append(y)
            adjacencies[y].append(x)
        curQ = [source]
        seen = set([source])
        nxtQ = []
        while curQ:
            x = curQ.pop()
            for y in adjacencies[x]:
                if y == destination:
                    return True
                if y not in seen:
                    seen.add(y)
                    nxtQ.append(y)
            if not curQ:
                curQ, nxtQ = nxtQ, curQ
        return False


class SolutionTest(unittest.TestCase):

    def test_sample1(self):
        sol = Solution()
        self.assertTrue(sol.validPath(3, [[0, 1], [1, 2], [2, 0]], 0, 2), True)

    def test_sample2(self):
        sol = Solution()
        self.assertTrue(sol.validPath(1, [], 0, 0), True)
