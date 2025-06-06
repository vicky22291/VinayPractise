"""
URL: https://leetcode.com/problems/frequency-of-the-most-frequent-element
"""
from typing import List


class Solution:
    def maxFrequency(self, nums: List[int], k: int) -> int:
        nums.sort()
        n = len(nums)
        left = cur = ans = 0
        for right in range(n):
            target = nums[right]
            cur += target

            if (right - left + 1) * target - cur > k:
                cur -= nums[left]
                left += 1
            ans = max(ans, right - left + 1)
        return ans