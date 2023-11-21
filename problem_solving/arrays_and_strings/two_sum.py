"""
    https://leetcode.com/problems/two-sum/description/
"""
from typing import List


class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        sNums = sorted([(index, num) for index, num in enumerate(nums)], key=lambda x: x[1])
        left = 0
        right = len(nums) - 1
        while left < right:
            s = sNums[left][1] + sNums[right][1]
            if s == target:
                return [sNums[left][0], sNums[right][0]]
            elif s > target:
                right -= 1
            else:
                left += 1
        return []
