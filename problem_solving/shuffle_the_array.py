"""
URL: https://leetcode.com/problems/shuffle-the-array
"""
from typing import List


class Solution:
    def shuffle(self, nums: List[int], n: int) -> List[int]:
        ans = []
        for i in range(n):
            ans.append(nums[i])
            ans.append(nums[n + i])
        return ans