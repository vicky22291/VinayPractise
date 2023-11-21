"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/127/strings/882/
"""
from collections import Counter


class Solution(object):
    def isAnagram(self, s, t):
        countS = Counter(s)
        countT = Counter(t)
        return not (countT - countS) and not (countS - countT)