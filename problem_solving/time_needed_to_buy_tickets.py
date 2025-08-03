"""
URL: https://leetcode.com/problems/time-needed-to-buy-tickets/description/?envType=company&envId=uber&favoriteSlug=uber-all
"""
from typing import List


class Solution:
    def timeRequiredToBuy(self, tickets: List[int], k: int) -> int:
        time = 0
        for i, ti in enumerate(tickets):
            if i <= k:
                time += min(tickets[k], ti)
            else:
                time += min(tickets[k] - 1, ti)
        return time