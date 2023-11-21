"""
    https://leetcode.com/problems/shortest-word-distance/description/
"""
import collections
import math
from typing import List


class Solution:
    def shortestDistance(self, wordsDict: List[str], word1: str, word2: str) -> int:
        indices = collections.defaultdict(list)
        for index, word in enumerate(wordsDict):
            indices[word].append(index)
        shortest = math.inf
        for w1I in indices[word1]:
            for w2I in indices[word2]:
                shortest = min(shortest, abs(w1I - w2I))
        return shortest