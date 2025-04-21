"""
URL: https://leetcode.com/problems/coin-change/

You are given an integer array coins representing coins of different denominations and an integer amount representing a total amount of money.

Return the fewest number of coins that you need to make up that amount. If that amount of money cannot be made up by any combination of the coins, return -1.

You may assume that you have an infinite number of each kind of coin.



Example 1:

Input: coins = [1,2,5], amount = 11
Output: 3
Explanation: 11 = 5 + 5 + 1
Example 2:

Input: coins = [2], amount = 3
Output: -1
Example 3:

Input: coins = [1], amount = 0
Output: 0


Constraints:

1 <= coins.length <= 12
1 <= coins[i] <= 231 - 1
0 <= amount <= 104
"""
from typing import List


class Solution:
    def coinChange(self, coins: List[int], amount: int) -> int:
        dp = [None for _ in range(amount + 1)]
        dp[0] = 0
        coins = sorted(coins)
        def dfs(target):
            if target < 0:
                return -1
            if dp[target] is not None:
                return dp[target]
            elif target < coins[0]:
                dp[target] = -1
            elif target in coins:
                dp[target] = 1
            else:
                vals = [dfs(target - coin) for coin in coins]
                if max(vals) == -1:
                    dp[target] = -1
                else:
                    min_val = 1_000_000_000
                    for val in vals:
                        if val != -1:
                            min_val = min(min_val, val)
                    dp[target] = min_val + 1
            return dp[target]
        return dfs(amount)