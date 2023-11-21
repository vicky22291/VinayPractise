"""
    https://leetcode.com/problems/find-words-that-can-be-formed-by-characters/
"""
import collections
from typing import List


class Solution:
    def countCharacters(self, words: List[str], chars: str) -> int:
        cc = collections.Counter(chars)
        ans = 0
        for word in words:
            cw = collections.Counter(word)
            if not (cw - cc):
                ans += len(word)
        return ans