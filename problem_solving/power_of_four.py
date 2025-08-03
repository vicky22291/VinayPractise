"""
URL: https://leetcode.com/problems/power-of-four/submissions/1721502018/?envType=company&envId=uber&favoriteSlug=uber-all
"""


class Solution:
    def isPowerOfFour(self, n: int) -> bool:
        if n < 1:
            return False
        while n % 4 == 0:
            n = n // 4
        return n == 1