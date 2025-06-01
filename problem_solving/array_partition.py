"""
URL: https://leetcode.com/problems/array-partition
"""
from typing import List


class Solution:
    def arrayPairSum(self, nums: List[int]) -> int:
        sn = sorted(nums)
        ans = 0
        for i in range(len(nums) // 2):
            ans += sn[2 * i]
        return ans