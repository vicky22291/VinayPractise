import unittest
from typing import List


"""
    https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/712/dynamic-programming/4585/
"""


"""
Alternative Solution
--------------------
class Solution:
    def uniquePathsWithObstacles(self, obstacleGrid: List[List[int]]) -> int:
        m, n = len(obstacleGrid), len(obstacleGrid[0])
        if obstacleGrid[m - 1][n - 1]:
            return 0
        
        @cache
        def dp(i, j):
            if i + j == 0:
                return 1
            ways = 0
            if i > 0 and obstacleGrid[i - 1][j] == 0:
                ways += dp(i - 1, j)
            if j > 0 and obstacleGrid[i][j - 1] == 0:
                ways += dp(i, j - 1)
            return ways

        return dp(m - 1, n - 1)
"""


class Solution:
    def uniquePathsWithObstacles(self, obstacleGrid: List[List[int]]) -> int:
        m, n = len(obstacleGrid), len(obstacleGrid[0])

        if obstacleGrid[0][0] == 1:
            return 0

        obstacleGrid[0][0] = 1

        for i in range(1, m):
            obstacleGrid[i][0] = int(obstacleGrid[i][0] == 0 and obstacleGrid[i - 1][0] == 1)

        for i in range(1, n):
            obstacleGrid[0][i] = int(obstacleGrid[0][i] == 0 and obstacleGrid[0][i - 1] == 1)

        for i in range(1, m):
            for j in range(1, n):
                if obstacleGrid[i][j]:
                    obstacleGrid[i][j] = 0
                else:
                    obstacleGrid[i][j] = obstacleGrid[i - 1][j] + obstacleGrid[i][j - 1]

        return obstacleGrid[m - 1][n - 1]


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(2, sol.uniquePathsWithObstacles([[0, 0, 0], [0, 1, 0], [0, 0, 0]]))
