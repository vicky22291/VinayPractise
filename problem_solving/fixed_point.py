"""
URL: https://leetcode.com/problems/fixed-point/description/?envType=company&envId=uber&favoriteSlug=uber-all
"""
from typing import List


class Solution:
    def fixedPoint(self, arr: List[int]) -> int:
        for i, num in enumerate(arr):
            if i == num:
                return i
        return -1