"""
    https://leetcode.com/problems/wiggle-sort/
"""


class Solution:
    def wiggleSort(self, nums: List[int]) -> None:
        copy = sorted(nums)
        n = len(nums)
        j = 0
        for i in range(n):
            if i % 2 == 0:
                nums[i] = copy[j]
            else:
                nums[i] = copy[n - j - 1]
                j += 1