"""
URL: https://leetcode.com/problems/check-if-string-is-a-prefix-of-array/description/?envType=company&envId=uber&favoriteSlug=uber-all
"""
from typing import List


class Solution:
    def isPrefixString(self, s: str, words: List[str]) -> bool:
        i, ls = 0, len(s)
        for w in words:
            lw = len(w)
            if not (i + lw <= ls and s[i:i + lw] == w):
                return False
            i = i + lw
            if i == ls:
                break
        return i == ls