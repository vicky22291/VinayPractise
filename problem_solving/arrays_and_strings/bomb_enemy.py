"""
    https://leetcode.com/problems/bomb-enemy/
"""
import collections
from bisect import bisect
from typing import List


class Solution:
    def maxKilledEnemies(self, grid: List[List[str]]) -> int:
        m, n = len(grid), len(grid[0])
        rData = collections.defaultdict(list)
        cData = collections.defaultdict(list)
        for i in range(m):
            rData[i].append([-1, 0])
            for j in range(n):
                if grid[i][j] == 'E':
                    rData[i][-1][1] += 1
                elif grid[i][j] == 'W':
                    rData[i].append([j, 0])
        for j in range(n):
            cData[j].append([-1, 0])
            for i in range(m):
                if grid[i][j] == 'E':
                    cData[j][-1][1] += 1
                elif grid[i][j] == 'W':
                    cData[j].append([i, 0])
        maxEnemies = 0
        for i in range(m):
            for j in range(n):
                if grid[i][j] == '0':
                    rI = bisect.bisect_left(rData[i], j, key=lambda x: x[0])
                    cI = bisect.bisect_left(cData[j], i, key=lambda x: x[0])
                    maxEnemies = max(maxEnemies, rData[i][rI - 1][1] + cData[j][cI - 1][1])
        return maxEnemies