"""
https://leetcode.com/explore/learn/card/dynamic-programming/632/common-patterns-in-dp-problems/4114/
"""
import unittest
from typing import List


class Solution:
    def lengthOfLIS(self, nums: List[int]) -> int:
        dp = [1] * len(nums)
        for i in range(1, len(nums)):
            for j in range(i):
                if nums[i] > nums[j]:
                    dp[i] = max(dp[i], dp[j] + 1)

        return max(dp)


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(4, sol.lengthOfLIS([10, 9, 2, 5, 3, 7, 101, 18]))

    def testSample2(self):
        sol = Solution()
        self.assertEqual(6, sol.lengthOfLIS([1, 3, 6, 7, 9, 4, 10, 5, 6]))
