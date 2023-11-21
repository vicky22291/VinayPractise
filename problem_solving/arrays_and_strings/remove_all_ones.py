"""
    https://leetcode.com/problems/remove-all-ones-with-row-and-column-flips/
"""
from typing import List


class Solution:
    def removeOnes(self, grid: List[List[int]]) -> bool:
        r1, r1_invert = grid[0], [1-val for val in grid[0]]
        for i in range(1, len(grid)):
            if grid[i] != r1 and grid[i] != r1_invert:
                return False
        return True