import unittest
from typing import List


"""
    Problem: https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/707/traversals-trees-graphs/4628/
    Using BFS
"""


class Solution:
    def maxAreaOfIsland(self, grid: List[List[int]]) -> int:
        def getEdges(x, y):
            return [(x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)]

        m = len(grid)
        n = len(grid[0])
        seen = set()
        maxArea = 0
        for x in range(m):
            for y in range(n):
                if (x, y) not in seen and grid[x][y]:
                    curArea = 1
                    seen.add((x, y))
                    curQ = [(x, y)]
                    nxtQ = []
                    while curQ:
                        cX, cY = curQ.pop()
                        for nX, nY in getEdges(cX, cY):
                            if 0 <= nX < m and 0 <= nY < n and grid[nX][nY] and (nX, nY) not in seen:
                                seen.add((nX, nY))
                                nxtQ.append((nX, nY))
                                curArea += 1
                        if not curQ:
                            curQ, nxtQ = nxtQ, curQ
                    maxArea = max(maxArea, curArea)
        return maxArea


class SolutionTests(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(6, sol.maxAreaOfIsland(
            [[0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0],
             [0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0],
             [0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
             [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0]]))
