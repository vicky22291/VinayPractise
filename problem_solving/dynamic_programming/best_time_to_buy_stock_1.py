"""
    https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/712/dynamic-programming/4583/
"""
from typing import List


class Solution:
    def maxProfit(self, prices: List[int], fee: int) -> int:
        n = len(prices)
        free, hold = 0, -prices[0]
        for i in range(1, n):
            free, hold = max(free, hold + prices[i] - fee), max(hold, free - prices[i])
        return free