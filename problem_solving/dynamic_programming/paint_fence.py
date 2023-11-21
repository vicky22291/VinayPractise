from functools import cache


"""
    https://leetcode.com/explore/learn/card/dynamic-programming/633/common-patterns-continued/4137/
"""


class Solution:
    def numWays(self, n: int, k: int) -> int:
        @cache
        def dp(i):
            if i == 1:
                return k
            elif i == 2:
                return k * k
            return (k - 1) * (dp(i - 1) + dp(i - 2))

        return dp(n)