"""
URL: https://leetcode.com/problems/ugly-number/?envType=company&envId=uber&favoriteSlug=uber-all
"""


class Solution:
    def isUgly(self, n: int) -> bool:
        for i in [2, 3, 5]:
            while n % i == 0:
                n = n / i
        return n == 1