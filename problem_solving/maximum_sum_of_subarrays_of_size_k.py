"""
Given an array of integers nums and an integer k, find the maximum sum of any contiguous subarray of size k.

Example 1: Input:

nums = [2, 1, 5, 1, 3, 2]
k = 3
Output:

9
Explanation: The subarray with the maximum sum is [5, 1, 3] with a sum of 9.
"""

class Solution:
    def maxSum(self, nums: list[int], k: int):
        max_sum = -float('inf')
        for i in range(len(nums) - k + 1):
            max_sum = max(sum(nums[i:i+k]), max_sum)
        return max_sum
