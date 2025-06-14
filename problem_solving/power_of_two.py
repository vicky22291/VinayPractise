"""
URL: https://leetcode.com/problems/power-of-two/description
"""


class Solution:
    def isPowerOfTwo(self, n: int) -> bool:
        n1s = 0
        while n > 0:
            n1s += n & 1
            n = n >> 1
        return n1s == 1