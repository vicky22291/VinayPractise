"""
URL: https://leetcode.com/problems/number-of-good-pairs/description/?envType=company&envId=uber&favoriteSlug=uber-all
"""
from collections import Counter
from typing import List


class Solution:
    def numIdenticalPairs(self, nums: List[int]) -> int:
        count = Counter(nums)
        ans = 0
        for val in count.values():
            ans += val * (val - 1) / 2
        return int(ans)