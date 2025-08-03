"""
URL: https://leetcode.com/problems/intersection-of-multiple-arrays/?envType=company&envId=uber&favoriteSlug=uber-all
"""
from typing import List


class Solution:
    def intersection(self, nums: List[List[int]]) -> List[int]:
        ans = set(nums[0])
        for arr in nums[1:]:
            ans = set(arr).intersection(ans)
        return sorted(list(ans))