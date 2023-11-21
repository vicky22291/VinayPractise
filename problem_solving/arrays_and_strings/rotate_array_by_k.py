"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/92/array/646/
"""
import unittest
from typing import List


class Solution:
    def rotate(self, nums: List[int], k: int) -> None:
        """
        Do not return anything, modify nums in-place instead.
        """
        n = len(nums)
        k = k % n
        arr = nums[n - k:] + nums[:n - k]
        for i in range(n):
            nums[i] = arr[i]


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        nums = [1, 2, 3, 4, 5, 6, 7]
        sol.rotate(nums, 3)
        self.assertEqual([5, 6, 7, 1, 2, 3, 4], nums)