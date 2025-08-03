"""
URL: https://leetcode.com/problems/points-that-intersect-with-cars/description/?envType=company&envId=uber&favoriteSlug=uber-all
"""
from typing import List


class Solution:
    def numberOfPoints(self, nums: List[List[int]]) -> int:
        sortedN = sorted(nums, key=lambda x: x[0])
        ans = 0
        pe = None
        for s, e in sortedN:
            if pe:
                if s > pe:
                    ans += e - s + 1
                elif e > pe:
                    ans += e - pe
                pe = max(e, pe)
            else:
                ans += e - s + 1
                pe = e
        return ans