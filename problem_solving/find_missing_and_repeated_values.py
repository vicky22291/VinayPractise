"""
URL: https://leetcode.com/problems/find-missing-and-repeated-values/description
"""
from typing import List


class Solution:
    def findMissingAndRepeatedValues(self, grid: List[List[int]]) -> List[int]:
        n = len(grid)
        to_be_seen = set([n for n in range(1, n * n + 1)])
        already_seen = None
        for i in range(n):
            for j in range(n):
                if grid[i][j] not in to_be_seen:
                    already_seen = grid[i][j]
                else:
                    to_be_seen.remove(grid[i][j])
        return [already_seen, list(to_be_seen)[0]]