"""
URL: https://leetcode.com/problems/number-of-strings-that-appear-as-substrings-in-word/description/?envType=company&envId=uber&favoriteSlug=uber-all
"""
from typing import List


class Solution:
    def numOfStrings(self, patterns: List[str], word: str) -> int:
        ans = 0
        for pat in patterns:
            if pat in word:
                ans += 1
        return ans