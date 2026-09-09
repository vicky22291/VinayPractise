"""
URL: https://leetcode.com/problems/find-all-numbers-disappeared-in-an-array/
"""


class Solution:
    def findDisappearedNumbers(self, nums: List[int]) -> List[int]:
        counts = [0] * len(nums)
        for i in nums:
            counts[i - 1] += 1
        result = []
        for x in range(1, len(nums) + 1):
            if counts[x - 1] == 0:
                result.append(x)
        return result