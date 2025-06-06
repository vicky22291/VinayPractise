"""
URL: https://leetcode.com/problems/count-nodes-equal-to-average-of-subtree
"""
from typing import List


class Solution:
    def missingElement(self, nums: List[int], k: int) -> int:
        diffs = []
        for i in range(1, len(nums)):
            diffs.append(nums[i] - nums[i - 1] - 1)
        i = 0
        while k > 0 and i < len(diffs):
            if k > diffs[i]:
                k -= diffs[i]
                i += 1
            else:
                break
        return nums[i] + k
