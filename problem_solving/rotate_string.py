"""
https://leetcode.com/problems/rotate-string/?envType=company&envId=google&favoriteSlug=google-all
"""
from collections import Counter


class Solution:
    def rotateString(self, s: str, goal: str) -> bool:
        if len(s) != len(goal):
            return False
        if s == goal:
            return True
        for i in range(len(s)):
            if s[i:] + s[:i] == goal:
                return True
        return False


sol = Solution()
print(sol.rotateString("dawhwh", "hdawhw"))