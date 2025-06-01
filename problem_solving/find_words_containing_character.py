"""
URL: https://leetcode.com/problems/find-words-containing-character
"""
from typing import List


class Solution:
    def findWordsContaining(self, words: List[str], x: str) -> List[int]:
        ans = []
        for index, word in enumerate(words):
            if x in word:
                ans.append(index)
        return ans
