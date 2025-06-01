"""
URL: https://leetcode.com/problems/three-consecutive-odds
"""
from typing import List


class Solution:
    def threeConsecutiveOdds(self, arr: List[int]) -> bool:
        s = None
        for e, num in enumerate(arr):
            if num % 2 == 0:
                s = None
            else:
                if s is None:
                    s = e
                elif e - s + 1 == 3:
                    return True
                else:
                    pass
        return False