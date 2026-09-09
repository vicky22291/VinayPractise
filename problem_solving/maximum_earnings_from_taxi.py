"""
URL: https://leetcode.com/problems/maximum-earnings-from-taxi/description
"""
from collections import defaultdict
from heapq import heappush
from typing import List


class Solution:
    def maxTaxiEarnings(self, n: int, rides: List[List[int]]) -> int:
        locBuckets = defaultdict(list)
        for start, end, tip in rides:
            heappush(locBuckets[end], (-(end - start + tip), start))
        dp = [0]
        for i in range(1, n):
            possibleEarnings = [dp[start - 1] - earning for earning, start in locBuckets[i + 1]]
            possibleEarnings.append(dp[-1])
            dp.append(max(possibleEarnings))
        return max(dp)

sol = Solution()
print(sol.maxTaxiEarnings(20, [[1,6,1],[3,10,2],[10,12,3],[11,12,2],[12,15,2],[13,18,1]]))