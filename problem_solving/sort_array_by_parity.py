"""
URL: https://leetcode.com/problems/sort-array-by-parity
"""
from typing import List


class Solution:
    def sortArrayByParity(self, nums: List[int]) -> List[int]:
        evens, odds = [], []
        for num in nums:
            if num % 2:
                odds.append(num)
            else:
                evens.append(num)
        evens.extend(odds)
        return evens