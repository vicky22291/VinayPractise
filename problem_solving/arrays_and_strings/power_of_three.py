"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/102/math/745/
"""


class Solution:
    def isPowerOfThree(self, n: int) -> bool:
        if n == 1:
            return True
        cur = 3
        while cur < n:
            cur *= 3
        return cur == n