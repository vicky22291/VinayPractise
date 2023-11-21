"""
https://leetcode.com/explore/learn/card/dynamic-programming/632/common-patterns-in-dp-problems/4113/
"""
from functools import cache
from typing import List


class Solution:
    def wordBreak(self, s: str, wordDict: List[str]) -> bool:
        @cache
        def dp(i):
            if i < 0:
                return True
            for word in wordDict:
                if i >= (len(word) - 1) and s[i - len(word) + 1: i + 1] == word and dp(i - len(word)):
                    return True
            return False

        return dp(len(s) - 1)
