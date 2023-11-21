from typing import List


"""
https://leetcode.com/explore/learn/card/dynamic-programming/631/strategy-for-solving-dp-problems/4148/
"""


class Solution:
    def rob(self, nums: List[int]) -> int:
        if len(nums) == 1:
            return nums[0]
        elif len(nums) == 2:
            return max(nums)
        a0, a1 = nums[0], max(nums[0], nums[1])
        ans = a1
        for num in nums[2:]:
            ans = max(a0 + num, a1)
            a0 = a1
            a1 = ans
        return ans