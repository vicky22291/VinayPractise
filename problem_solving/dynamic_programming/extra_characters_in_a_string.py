"""
    https://leetcode.com/problems/extra-characters-in-a-string/?envType=daily-question&envId=2023-09-02
"""
import math
import unittest
from functools import cache
from typing import List


class Solution:
    def minExtraChar(self, s: str, dictionary: List[str]) -> int:
        data = set(dictionary)

        @cache
        def dp(i, j):
            nonlocal data
            if s[i:j+1] in data:
                return 0
            elif i == j:
                return 1
            minimum = math.inf
            for k in range(i, j):
                minimum = min(minimum, dp(i, k) + dp(k + 1, j))
            return minimum

        return dp(0, len(s) - 1)


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(1, sol.minExtraChar("leetscode", ["leet", "code", "leetcode"]))
