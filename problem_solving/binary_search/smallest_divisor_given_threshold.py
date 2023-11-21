"""
    https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/710/binary-search/4694/
"""
import math
import unittest
from typing import List


class Solution:
    def smallestDivisor(self, nums: List[int], threshold: int) -> int:
        def getSum(nums, divisor):
            return sum([math.ceil(num / divisor) for num in nums])

        left = 1
        right = max(nums)
        while left <= right:
            mid = (left + right) // 2
            sumForMidDivisor = getSum(nums, mid)
            if sumForMidDivisor <= threshold:
                right = mid - 1
            else:
                left = mid + 1
        return left


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(5, sol.smallestDivisor([1, 2, 5, 9], 6))

    def testSample2(self):
        sol = Solution()
        self.assertEqual(44, sol.smallestDivisor([44, 22, 33, 11, 1], 5))

    def testSample3(self):
        sol = Solution()
        self.assertEqual(34, sol.smallestDivisor([200, 100, 14], 10))
