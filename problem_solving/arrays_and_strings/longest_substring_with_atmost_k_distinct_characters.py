"""
    https://leetcode.com/explore/interview/card/top-interview-questions-hard/116/array-and-strings/835/
"""
import unittest


class Solution:
    def lengthOfLongestSubstringKDistinct(self, s: str, k: int) -> int:
        if k == 0:
            return 0
        distinct = startIndex = maximum = 0
        counter = {}
        for i in range(len(s)):
            if s[i] not in counter or counter[s[i]] == 0:
                while distinct == k:
                    counter[s[startIndex]] -= 1
                    if counter[s[startIndex]] == 0:
                        distinct -= 1
                    startIndex += 1
                if s[i] not in counter:
                    counter[s[i]] = 0
                distinct += 1
            counter[s[i]] += 1
            maximum = max(maximum, i - startIndex + 1)
        maximum = max(maximum, len(s) - startIndex)
        return maximum


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(3, sol.lengthOfLongestSubstringKDistinct("eceba", 2))