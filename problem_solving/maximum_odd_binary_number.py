"""
URL: https://leetcode.com/problems/maximum-odd-binary-number
"""
from collections import Counter


class Solution:
    def maximumOddBinaryNumber(self, s: str) -> str:
        count = Counter(s)
        arr = ["1" * (count["1"] - 1)]
        arr.extend(["0" * (count["0"])])
        arr.append("1")
        return "".join(arr)