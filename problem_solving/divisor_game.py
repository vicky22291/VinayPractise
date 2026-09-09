"""
URL: https://leetcode.com/problems/divisor-game
"""


class Solution:
    def divisorGame(self, n: int) -> bool:
        dp = [False] * (n + 1)
        for k in range(2, n + 1):
            dp[k] = any(k % x == 0 and not dp[k - x] for x in range(1, k))
        return dp[n]


sol = Solution()
print(sol.divisorGame(2))
print(sol.divisorGame(3))
print(sol.divisorGame(4))
