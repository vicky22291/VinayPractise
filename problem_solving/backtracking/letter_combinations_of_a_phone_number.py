"""
    https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/711/backtracking/4577/
"""
from typing import List


class Solution:
    def letterCombinations(self, digits: str) -> List[str]:
        keys = ['abc', 'def', 'ghi', 'jkl', 'mno', 'pqrs', 'tuv', 'wxyz']
        n = len(digits)

        result = []

        if n == 0:
            return result

        def dfs(i, visited):
            if i == n:
                result.append("".join(visited))
                return
            for char in keys[int(digits[i]) - 2]:
                visited.append(char)
                dfs(i + 1, visited)
                visited.pop()

        dfs(0, [])

        return result