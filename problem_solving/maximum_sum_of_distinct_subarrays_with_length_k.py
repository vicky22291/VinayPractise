"""
URL: https://leetcode.com/problems/maximum-sum-of-distinct-subarrays-with-length-k/description/
"""
from collections import Counter, defaultdict
from typing import List


class Solution:
    def maximumSubarraySum(self, nums: List[int], k: int) -> int:
        ans = current_sum = begin = end = 0
        num_to_index = {}

        while end < len(nums):
            curr_num = nums[end]
            last_occurrence = num_to_index.get(curr_num, -1)
            # if current window already has number or if window is too big, adjust window
            while begin <= last_occurrence or end - begin + 1 > k:
                current_sum -= nums[begin]
                begin += 1
            num_to_index[curr_num] = end
            current_sum += nums[end]
            if end - begin + 1 == k:
                ans = max(ans, current_sum)
            end += 1
        return ans
