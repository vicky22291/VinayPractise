"""
    https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/711/backtracking/4695/
"""
from typing import List


class Solution:
    def numsSameConsecDiff(self, n: int, k: int) -> List[int]:
        result = []

        def dfs(i, num):
            if i == n:
                result.append(num)
            elif i == 0:
                for j in range(1, 10):
                    dfs(i + 1, num * 10 + j)
            else:
                for j in range(10):
                    if abs(num % 10 - j) == k:
                        dfs(i + 1, num * 10 + j)

        dfs(0, 0)
        return result
