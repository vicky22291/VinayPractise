"""
https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/711/backtracking/4575/
"""


import unittest
from typing import List


class Solution:
    def allPathsSourceTarget(self, graph: List[List[int]]) -> List[List[int]]:
        n = len(graph)
        result = []

        def dfs(node, visited):
            nonlocal n, result
            visited.append(node)
            if node == n - 1:
                result.append([inode for inode in visited])
            else:
                for dep in graph[node]:
                    dfs(dep, visited)
            visited.pop()

        dfs(0, [])
        return result


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual([[0, 1, 3], [0, 2, 3]], sol.allPathsSourceTarget([[1, 2], [3], [3], []]))
