"""
URL: https://leetcode.com/problems/cutting-ribbons
"""
from typing import List


class Solution:
    def maxLength(self, ribbons: List[int], k: int) -> int:
        def isPossible(x):
            nonlocal ribbons, k
            t = 0
            for num in ribbons:
                t += num // x
                if t >= k:
                    return True
            return False
        left, right = 0, max(ribbons)
        while left < right:
            mid = (left + right + 1) // 2
            if isPossible(mid):
                left = mid
            else:
                right = mid - 1
        return left
