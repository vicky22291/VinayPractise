"""
URL: https://leetcode.com/problems/maximum-points-you-can-obtain-from-cards/description/
"""
from typing import List


class Solution:
    def maxScore(self, cardPoints: List[int], k: int) -> int:
        full_sum = sum(cardPoints)
        n = len(cardPoints)
        min_sum = 1_000_000_000_000
        t = n - k
        first_sum = None
        for i in range(n - t + 1):
            if first_sum is None:
                first_sum = sum(cardPoints[:t])
            else:
                first_sum -= cardPoints[i - 1]
                first_sum += cardPoints[i + t - 1]
            min_sum = min(first_sum, min_sum)
        return full_sum - min_sum