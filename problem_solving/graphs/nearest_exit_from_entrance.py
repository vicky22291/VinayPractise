import unittest
from typing import List


class Solution:
    def nearestExit(self, maze: List[List[str]], entrance: List[int]) -> int:
        def getEdges(x, y):
            return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

        m = len(maze)
        n = len(maze[0])
        seen = set([tuple(entrance)])
        curQ = [tuple(entrance)]
        nxtQ = []
        stepsCount = 1
        while curQ:
            x, y = curQ.pop()
            for nX, nY in getEdges(x, y):
                if 0 <= nX < m and 0 <= nY < n:
                    if (nX, nY) not in seen and maze[nX][nY] == '.':
                        if nX in [0, m - 1] or nY in [0, n - 1]:
                            return stepsCount
                        seen.add((nX, nY))
                        nxtQ.append((nX, nY))
            if not curQ:
                curQ, nxtQ = nxtQ, curQ
                stepsCount += 1
        return -1


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(2, sol.nearestExit([["+", "+", "+"], [".", ".", "."], ["+", "+", "+"]], [1, 0]))

    def testSample2(self):
        sol = Solution()
        self.assertEqual(1, sol.nearestExit([["+", "+", ".", "+"], [".", ".", ".", "+"], ["+", "+", "+", "."]], [1, 2]))

    def testSample3(self):
        sol = Solution()
        self.assertEqual(12, sol.nearestExit([["+", ".", "+", "+", "+", "+", "+"], ["+", ".", "+", ".", ".", ".", "+"],
                                              ["+", ".", "+", ".", "+", ".", "+"], ["+", ".", ".", ".", "+", ".", "+"],
                                              ["+", "+", "+", "+", "+", ".", "+"]], [0, 1]))
