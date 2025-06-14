"""
URL: https://leetcode.com/problems/maximum-difference-between-even-and-odd-frequency-i/description
"""
from collections import Counter


class Solution:
    def maxDifference(self, s: str) -> int:
        count = Counter(s)
        even = 1_000_000_000
        odd = 0
        for _, value in count.items():
            if value % 2:
                odd = max(odd, value)
            else:
                even = min(even, value)
        return odd - even