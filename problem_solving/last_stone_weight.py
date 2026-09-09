"""
URL: https://leetcode.com/problems/last-stone-weight/
"""
import heapq
from typing import List


class Solution:
    def lastStoneWeight(self, stones: List[int]) -> int:
        heapq.heapify_max(stones)
        while (len(stones) > 1):
            y, x = heapq.heappop_max(stones), heapq.heappop_max(stones)
            if x < y:
                heapq.heappush_max(stones, y - x)
        return 0 if len(stones) == 0 else stones[0]


sol = Solution()
# print(sol.lastStoneWeight([2,7,4,1,8,1]))
print(sol.lastStoneWeight([4,3,4,3,2]))