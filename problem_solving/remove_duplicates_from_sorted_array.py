"""
URL: https://leetcode.com/problems/remove-duplicates-from-sorted-array/description
"""
from typing import List


class Solution:
    def removeDuplicates(self, nums: List[int]) -> int:
        n = 0
        prev = None
        for num in nums:
            if prev is None or prev != num:
                nums[n] = num
                n += 1
            prev = num
        return n