"""
URL: https://leetcode.com/problems/max-consecutive-ones/description
"""
from typing import List


class Solution:
    def findMaxConsecutiveOnes(self, nums: List[int]) -> int:
        left, right, n, max_len = -1, 0, len(nums), 0
        while right < n:
            if nums[right] != 1:
                left = right
            else:
                max_len = max(max_len, right - left)
            right += 1
        return max_len