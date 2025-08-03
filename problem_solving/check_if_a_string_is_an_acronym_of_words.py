"""
URL: https://leetcode.com/problems/check-if-a-string-is-an-acronym-of-words/description/?envType=company&envId=uber&favoriteSlug=uber-all
"""
from typing import List


class Solution:
    def isAcronym(self, words: List[str], s: str) -> bool:
        if len(words) != len(s):
            return False
        for i, w in enumerate(words):
            if s[i] != w[0]:
                return False
        return True