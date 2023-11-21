"""
https://leetcode.com/explore/learn/card/dynamic-programming/631/strategy-for-solving-dp-problems/4041/
"""


class Solution:
    def tribonacci(self, n: int) -> int:
        if n == 0:
            return 0
        elif n <= 2:
            return 1
        a0, a1, a2 = 0, 1, 1
        for i in range(3, n + 1):
            a0, a1, a2 = a1, a2, a0 + a1 + a2
        return a2