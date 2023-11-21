"""
    https://leetcode.com/problems/find-all-good-indices/description/
"""
from typing import List


class Solution:
    def goodIndices(self, nums: List[int], k: int) -> List[int]:
        if k == 1:
            return list(range(1, len(nums) - 1))

        decMap = {}
        decCurrInd = 0
        incCurrInd = k + 1
        ans = []

        for i in range(1, len(nums) - k - 1):
            if nums[i] > nums[i - 1]:
                decCurrInd = i
            if i - decCurrInd + 1 == k:
                decMap[decCurrInd + k + 1] = decCurrInd
                decCurrInd += 1

        for i in range(k + 2, len(nums)):
            if nums[i] < nums[i - 1]:
                incCurrInd = i
            if i - incCurrInd + 1 == k:

                if incCurrInd in decMap:
                    ans.append(incCurrInd - 1)
                incCurrInd += 1
        return ans