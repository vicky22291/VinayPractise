"""
    https://leetcode.com/problems/sentence-screen-fitting/description/
"""
from functools import cache
from typing import List


class Solution:
    def wordsTyping(self, sentence: List[str], rows: int, cols: int) -> int:
        """
        lS = [len(word) for word in sentence]
        plS = [lS[0]]
        for l in lS[1:]:
            plS.append(plS[-1] + l)
        count = 0
        sI = 0
        for row in range(rows):
            col = cols
            while col > 0:
                word = sentence[sI]
                if col >= len(word):
                    col -= len(word) + 1
                    sI += 1
                    if sI == len(sentence):
                        count += 1
                        sI = 0
                else:
                    col = 0
        return count
        """
        n = len(sentence)

        @cache
        def fit(i):
            curr = 0
            times = 0
            while (curr + len(sentence[i])) <= cols:
                curr += len(sentence[i]) + 1
                i += 1
                if i == n:
                    i = 0
                    times += 1
            return i, times

        ans = 0
        i = 0
        for _ in range(rows):
            i, times = fit(i)
            ans += times

        return ans