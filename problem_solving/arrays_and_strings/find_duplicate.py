"""
    https://leetcode.com/problems/find-the-duplicate-number/submissions/
"""
from typing import List


class Solution:
    def findDuplicate(self, nums: List[int]) -> int:
        while nums[0] != nums[nums[0]]:
            nums[nums[0]], nums[0] = nums[0], nums[nums[0]]
        return nums[0]