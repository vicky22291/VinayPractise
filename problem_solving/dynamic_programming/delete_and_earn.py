import collections
import unittest
from functools import cache
from typing import List


class Solution:
    def deleteAndEarn(self, nums: List[int]) -> int:
        data = {num: num * count for num, count in collections.Counter(nums).items()}

        @cache
        def dp(num):
            if num == 0:
                return 0
            if num == 1:
                return data[1] if 1 in data else 0
            if num not in data:
                return dp(num - 1)
            return max(dp(num - 1), dp(num - 2) + data[num])

        return dp(max(nums))


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(6, sol.deleteAndEarn([3, 4, 2]))
