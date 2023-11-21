"""
    https://leetcode.com/problems/count-good-numbers/description/
"""
import math


class Solution:
    MOD = int(1e9+7)

    @staticmethod
    def binexp(a, b, MOD):
        a %= MOD
        res = 1

        while b > 0:
            if b & 1:
                res = res * a % MOD
            a = a * a % MOD
            b >>= 1

        return res

    def countGoodNumbers(self, n: int) -> int:
        odds = math.floor(n/2)
        evens = math.ceil(n/2)
        return int(self.binexp(5, evens, self.MOD) * self.binexp(4, odds, self.MOD) % self.MOD)