"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/97/dynamic-programming/566/
"""
from typing import List


class Solution:
    def maxSubArray(self, nums: List[int]) -> int:
        currentSum = maxSum = nums[0]
        for num in nums[1:]:
            currentSum = max(num, currentSum + num)
            maxSum = max(maxSum, currentSum)
        return maxSum