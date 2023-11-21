"""
    https://leetcode.com/problems/richest-customer-wealth/
"""
from typing import List


class Solution:
    def maximumWealth(self, accounts: List[List[int]]) -> int:
        maxWealth = 0
        for row in accounts:
            maxWealth = max(maxWealth, sum(row))
        return maxWealth