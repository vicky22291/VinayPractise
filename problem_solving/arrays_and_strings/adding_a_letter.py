"""
    https://leetcode.com/problems/count-words-obtained-after-adding-a-letter/
"""
import collections
from typing import List


"""
    Improvised solution would be to sort all the Words, based on length. And Skip all lengths that greater than 1 for comparison.
    And seen is anyhow required.
"""


class Solution:
    def wordCount(self, startWords: List[str], targetWords: List[str]) -> int:
        count = 0
        tWCount = collections.Counter(targetWords)
        possible = set()
        for word in startWords:
            cW = collections.Counter(word)
            for tWord in targetWords:
                if tWord not in possible:
                    cTW = collections.Counter(tWord)
                    if len(cW - cTW) == 0 and len(cTW - cW) == 1:
                        possible.add(tWord)
                        count += tWCount[tWord]
        return count