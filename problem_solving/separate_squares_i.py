"""
URL: https://leetcode.com/problems/separate-squares-i/description
"""
from typing import List


class Solution:
    def separateSquares(self, squares: List[List[int]]) -> float:
        def difference(line: float) -> float:
            above = below = 0.0
            for x, y, l in squares:
                if line <= y:
                    above += l * l
                elif line >= y + l:
                    below += l * l
                else:
                    above += l * ((y + l) - line)
                    below += l * (line - y)
            return above - below

        lo, hi = 0, 2 * 1e9
        for _ in range(60):
            mid = (lo + hi) / 2.0
            diff = difference(mid)
            if diff > 0:
                lo = mid
            else:
                hi = mid
        return hi