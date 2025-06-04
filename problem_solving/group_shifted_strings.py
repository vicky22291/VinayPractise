"""
URL: https://leetcode.com/problems/group-shifted-strings
"""
from collections import defaultdict
from typing import List


class Solution:
    def groupStrings(self, strings: List[str]) -> List[List[str]]:
        groups = defaultdict(list)
        for string in strings:
            fChar = string[0]
            if fChar == "a":
                groups[string].append(string)
                continue
            distance = ord(fChar) - ord("a")
            shifted_chars = []
            for char in string:
                ordC = ord(char) - distance
                if ordC < ord("a"):
                    ordC += 26
                shifted_chars.append(chr(ordC))
            gString = "".join(shifted_chars)
            groups[gString].append(string)
        ans = []
        for key, value in groups.items():
            ans.append(value)
        return ans