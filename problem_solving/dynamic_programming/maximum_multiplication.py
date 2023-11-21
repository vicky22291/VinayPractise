from functools import cache
from typing import List


"""
https://leetcode.com/explore/learn/card/dynamic-programming/631/strategy-for-solving-dp-problems/4146/
"""


"""
Top Down
class Solution:
    def maximumScore(self, nums: List[int], multipliers: List[int]) -> int:
        n = len(nums)
        m = len(multipliers)

        @cache
        def dp(i, left):
            nonlocal m, n, nums, multipliers
            if i == m:
                return 0
            right = n - 1 - (i - left)
            return max(dp(i + 1, left + 1) + multipliers[i] * nums[left],
                       dp(i + 1, left) + multipliers[i] * nums[right])

        return dp(0, 0)
"""

"""
Bottom Up
class Solution:
    def maximumScore(self, nums: List[int], multipliers: List[int]) -> int:
        n = len(nums)
        m = len(multipliers)

        dp = [[0] * (m + 1) for _ in range(m + 1)]

        for i in range(m - 1, -1, -1):
            for l in range(i, -1, -1):
                right = n - 1 - (i - l)
                dp[i][l] = max(dp[i + 1][l + 1] + multipliers[i] * nums[l],
                               dp[i + 1][l] + multipliers[i] * nums[right])

        return dp[0][0]
"""


class Solution:
    def maximumScore(self, nums: List[int], multipliers: List[int]) -> int:

        m = len(multipliers)
        n = len(nums)

        dp = [0] * (m + 1)

        for op in range(m - 1, -1, -1):
            for left in range(0, op+1, 1):
                dp[left] = max(multipliers[op] * nums[left] + dp[left + 1],
                               multipliers[op] * nums[n - 1 - (op - left)] + dp[left])

        return dp[0]
