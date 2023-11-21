"""
https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/712/dynamic-programming/4580/
"""


class Solution:
    def climbStairs(self, n: int) -> int:
        if n == 1:
            return 1
        elif n == 2:
            return 2
        n1 = 1
        n2 = 2
        cur = 0
        for i in range(2, n):
            cur, n1 = n1 + n2, n2
            n2 = cur
        return cur