"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/92/array/567/
"""
from typing import List


class Solution:
    def moveZeroes(self, nums: List[int]) -> None:
        """
        Do not return anything, modify nums in-place instead.
        """
        i = 0
        for num in nums:
            if num != 0:
                nums[i] = num
                i += 1
        while i < len(nums):
            nums[i] = 0
            i += 1