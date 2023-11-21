"""
    https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/711/backtracking/4683/
"""
from typing import List


class Solution:
    def combinationSum3(self, k: int, n: int) -> List[List[int]]:
        result = []

        def dfs(i, curSum, visited):
            if i == k and curSum == 0:
                result.append([num for num in visited])
            elif curSum < 0:
                return
            else:
                lastNum = visited[-1] if visited else 0
                for j in range(lastNum + 1, 10):
                    visited.append(j)
                    dfs(i + 1, curSum - j, visited)
                    visited.pop()

        dfs(0, n, [])
        return result