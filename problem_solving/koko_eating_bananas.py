"""
URL: https://leetcode.com/problems/koko-eating-bananas/
"""
from math import ceil
from typing import List


class Solution:
    def minEatingSpeed(self, piles: List[int], h: int) -> int:
        if len(piles) == h:
            return max(piles)
        left, right = 1, max(piles)
        while left < right:
            middle = (left + right) // 2
            hours = 0
            for pile in piles:
                hours += ceil(pile / middle)
            if hours <= h:
                right = middle
            else:
                left = middle + 1
        return right