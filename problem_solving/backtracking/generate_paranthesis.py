"""
    https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/711/backtracking/4578/
"""
import unittest
from typing import List


class Solution:
    def generateParenthesis(self, n: int) -> List[str]:
        result = []
        data = {
            '(': 1,
            ')': -1
        }

        def dfs(i, string, curSum):
            nonlocal n
            if i == 2 * n:
                if curSum == 0:
                    result.append("".join(string))
            elif curSum < 0:
                return
            else:
                for key, value in data.items():
                    string.append(key)
                    dfs(i + 1, string, curSum + value)
                    string.pop()

        dfs(0, [], 0)
        return list(result)


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(["((()))", "(()())", "(())()", "()(())", "()()()"], sol.generateParenthesis(3))
