"""
URL: https://leetcode.com/problems/optimal-account-balancing
"""
import collections
from typing import List


class Solution:
    def minTransfers(self, transactions: List[List[int]]) -> int:
        balance_map = collections.defaultdict(int)
        for a, b, amount in transactions:
            balance_map[a] += amount
            balance_map[b] -= amount

        balance_list = [amount for amount in balance_map.values() if amount]
        n = len(balance_list)

        def dfs(cur):
            while cur < n and not balance_list[cur]:
                cur += 1
            if cur == n:
                return 0
            cost = float('inf')
            for nxt in range(cur + 1, n):
                if balance_list[nxt] * balance_list[cur] < 0:
                    balance_list[nxt] += balance_list[cur]
                    cost = min(cost, 1 + dfs(cur + 1))
                    balance_list[nxt] -= balance_list[cur]
            return cost

        return dfs(0)