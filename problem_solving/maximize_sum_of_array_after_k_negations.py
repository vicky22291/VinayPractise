"""
URL: https://leetcode.com/problems/maximize-sum-of-array-after-k-negations
"""
import heapq
from typing import List


class Solution:
    def largestSumAfterKNegations(self, nums: List[int], k: int) -> int:
        heapq.heapify(nums)
        for _ in range(k):
            smallest = heapq.heappop(nums)
            heapq.heappush(nums, -smallest)
        return sum(nums)

