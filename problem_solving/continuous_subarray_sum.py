"""
URL: https://leetcode.com/problems/continuous-subarray-sum
"""
from typing import List


class Solution:
    def checkSubarraySum(self, nums: List[int], k: int) -> bool:
        pMod = 0
        mod_seen = {0: -1}
        for i in range(len(nums)):
            pMod = (pMod + nums[i]) % k
            if pMod in mod_seen:
                if i - mod_seen[pMod] > 1:
                    return True
            else:
                mod_seen[pMod] = i
        return False