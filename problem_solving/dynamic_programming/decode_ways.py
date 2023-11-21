import unittest
from functools import cache


class Solution:
    def numDecodings(self, s: str) -> int:
        @cache
        def dp(i, string):
            nonlocal s
            if i >= len(s):
                return 1
            oneDigit = twoDigit = 0
            if 0 < int(s[i]) < 10:
                subAns = dp(i + 1, s[i])
                if subAns:
                    oneDigit = subAns
            if i + 1 < len(s) and 10 <= int(s[i: i + 2]) <= 26:
                subAns = dp(i + 2, s[i: i + 2])
                if subAns:
                    twoDigit = subAns
            return oneDigit + twoDigit

        return dp(0, '')


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(2, sol.numDecodings("12"))

    def testSample2(self):
        sol = Solution()
        self.assertEqual(3, sol.numDecodings("226"))

    def testSample3(self):
        sol = Solution()
        self.assertEqual(1, sol.numDecodings("10"))