"""
    https://leetcode.com/problems/shortest-unsorted-continuous-subarray/
"""
import unittest
from typing import List


class Solution:
    def findUnsortedSubarray(self, nums: List[int]) -> int:
        start = -1
        prev = None
        for i, num in enumerate(nums):
            if prev is not None and prev > num:
                start = i - 1
                break
            prev = num

        prev = None
        end = -1
        for i in range(len(nums) - 1, -1, -1):
            if prev is not None and prev < nums[i]:
                end = i + 1
                break
            prev = nums[i]

        if end == -1:
            return 0

        smallest = min(nums[start: (end + 1)])
        largest = max(nums[start: (end + 1)])

        while start > -1:
            if nums[start] > smallest:
                start -= 1
            else:
                break
        while end < len(nums):
            if nums[end] < largest:
                end += 1
            else:
                break
        start = start + 1

        return end - start


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(5, sol.findUnsortedSubarray([2, 6, 4, 8, 10, 9, 15]))

    def testSample2(self):
        sol = Solution()
        self.assertEqual(0, sol.findUnsortedSubarray([1, 2, 3, 4]))

    def testSample3(self):
        sol = Solution()
        self.assertEqual(0, sol.findUnsortedSubarray([1]))
