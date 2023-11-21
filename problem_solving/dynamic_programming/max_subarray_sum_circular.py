import unittest
from typing import List


"""
    https://leetcode.com/explore/learn/card/dynamic-programming/633/common-patterns-continued/4142/
"""


class Solution:
    def maxSubarraySumCircular(self, nums: List[int]) -> int:
        cur_max = 0
        cur_min = 0
        _sum = 0
        max_sum = nums[0]
        min_sum = nums[0]
        for num in nums:
            cur_max = max(cur_max, 0) + num
            max_sum = max(max_sum, cur_max)
            cur_min = min(cur_min, 0) + num
            min_sum = min(min_sum, cur_min)
            _sum += num
        return max_sum if _sum == min_sum else max(max_sum, _sum - min_sum)


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(3, sol.maxSubarraySumCircular([1, -2, 3, -2]))
