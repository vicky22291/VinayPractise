"""
    https://leetcode.com/problems/greatest-common-divisor-of-strings/
"""


class Solution:
    def gcdOfStrings(self, str1: str, str2: str) -> str:
        if len(str1) > len(str2):
            str1, str2 = str2, str1
        m, n = len(str1), len(str2)
        for i in range(m - 1, -1, -1):
            sub = str1[:i + 1]
            x = len(sub)
            if m % x == 0 and n % x == 0 and \
                    "".join([sub] * (m // x)) == str1 and \
                    "".join([sub] * (n // x)) == str2:
                return sub
        return ""