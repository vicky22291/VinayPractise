"""
URL: https://leetcode.com/problems/find-the-difference/
"""
from collections import Counter


class Solution:
    def findTheDifference(self, s: str, t: str) -> str:
        count_s = Counter(s)
        count_t = Counter(t)
        for key in count_t:
            if count_s[key] != count_t[key]:
                return key
        return ""


sol = Solution()
print(sol.findTheDifference("abcd", "abcde"))