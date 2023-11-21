import unittest
from typing import List


"""
    https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/710/binary-search/4569/
"""


class Solution:
    def searchInsert(self, nums: List[int], target: int) -> int:
        left = 0
        right = len(nums)
        while left < right:
            mid = (left + right) // 2
            if nums[mid] == target:
                return mid
            elif nums[mid] < target:
                left = mid + 1
            else:
                right = mid
        return left


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(2, sol.searchInsert([1, 3, 5, 6], 5))

    def testSample2(self):
        sol = Solution()
        self.assertEqual(1, sol.searchInsert([1, 3, 5, 6], 2))

    def testSample3(self):
        sol = Solution()
        self.assertEqual(4, sol.searchInsert([1, 3, 5, 6], 7))

    def testSample4(self):
        sol = Solution()
        self.assertEqual(1, sol.searchInsert([1, 3], 2))
