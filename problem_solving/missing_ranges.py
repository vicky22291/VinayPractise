"""
URL: https://leetcode.com/problems/missing-ranges/description
"""
from typing import List


class Solution:
    def findMissingRanges(self, nums: List[int], lower: int, upper: int) -> List[List[int]]:
        l, r = lower, upper
        i, n = 0, len(nums)
        ans = []
        while l <= r and i < n:
            if l <= nums[i] - 1:
                ans.append([l, nums[i] - 1])
            l = nums[i] + 1
            i += 1
        if l <= r:
            ans.append([l, r])
        return ans