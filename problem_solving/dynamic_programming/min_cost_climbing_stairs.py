from typing import List


"""
    https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/712/dynamic-programming/4684/
"""


class Solution:
    def minCostClimbingStairs(self, cost: List[int]) -> int:
        c0 = c1 = 0
        n = len(cost)
        cur = 0
        for i in range(2, n + 1):
            cur = min(c0 + cost[i - 2], c1 + cost[i - 1])
            c0, c1 = c1, cur
        return cur