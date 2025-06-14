"""
URL: https://leetcode.com/problems/maximum-difference-between-adjacent-elements-in-a-circular-array/description
"""
from typing import List


class Solution:
    def maxAdjacentDistance(self, nums: List[int]) -> int:
        max_dist = 0
        for i in range(1, len(nums)):
            if i == len(nums) - 1:
                max_dist = max(max_dist, abs(nums[i] - nums[i - 1]), abs(nums[i] - nums[0]))
            else:
                max_dist = max(max_dist, abs(nums[i] - nums[i - 1]))
        return max_dist