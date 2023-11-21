"""
    https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/712/dynamic-programming/4584/
"""
from typing import List


class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        sold, held, reset = float('-inf'), float('-inf'), 0
        for price in prices:
            sold, held, reset = held + price, max(held, reset - price), max(reset, sold)
        return max(sold, reset)