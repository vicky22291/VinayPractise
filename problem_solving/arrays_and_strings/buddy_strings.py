"""
    https://leetcode.com/problems/buddy-strings/
"""
import collections
import unittest


class Solution:
    def buddyStrings(self, s: str, goal: str) -> bool:
        if len(s) != len(goal):
            return False
        if s == goal:
            countS = collections.Counter(s)
            for char, val in countS.items():
                if val > 1:
                    return True

        data = []
        s = list(s)
        for i, char in enumerate(s):
            if char != goal[i]:
                if len(data) < 2:
                    data.append(i)
                if len(data) == 2:
                    s[data[0]], s[data[1]] = s[data[1]], s[data[0]]
                    if "".join(s) == goal:
                        return True
        return False


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertTrue(sol.buddyStrings("aa", "aa"))