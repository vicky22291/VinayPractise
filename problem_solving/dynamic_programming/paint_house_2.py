import math
from functools import cache
from typing import List


"""
    https://leetcode.com/explore/learn/card/dynamic-programming/647/more-practice-problems/4075/
"""


class Solution:
    def minCostII(self, costs: List[List[int]]) -> int:
        k = len(costs[0])
        @cache
        def dp(i, c):
            minimum = math.inf
            for j in range(k):
                if j != c:
                    if i == 0:
                        minimum = min(minimum, costs[i][j])
                    else:
                        minimum = min(minimum, costs[i][j] + dp(i - 1, j))
            return minimum

        finalMin = math.inf
        for j in range(k):
            finalMin = min(finalMin, dp(len(costs) - 1, j))
        return finalMin