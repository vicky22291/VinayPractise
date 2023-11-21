"""
    https://leetcode.com/explore/learn/card/dynamic-programming/634/matrix-path-based-dp/4130/
"""
from functools import cache


class Solution:
    def uniquePaths(self, m: int, n: int) -> int:
        @cache
        def dp(i, j):
            if i + j == 0:
                return 1
            ways = 0
            if i > 0:
                ways += dp(i - 1, j)
            if j > 0:
                ways += dp(i, j - 1)
            return ways

        return dp(m - 1, n - 1)
