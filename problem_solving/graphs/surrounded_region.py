"""
    https://leetcode.com/explore/interview/card/top-interview-questions-hard/118/trees-and-graphs/843/
"""
import unittest
from typing import List


class Solution:
    def solve(self, board: List[List[str]]) -> None:
        m, n = len(board), len(board[0])
        os = set()
        seen = set()
        for i in range(m):
            for j in range(n):
                if board[i][j] == 'O':
                    os.add((i, j))

        def bfs(i, j, seen):
            region = set()
            q = [(i, j)]
            seen.add((i, j))
            hasBorder = False
            nq = []
            while q:
                x, y = q.pop()
                if x in [0, m - 1] or y in [0, n - 1]:
                    hasBorder = True
                region.add((x, y))
                for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                    if 0 <= x + dx < m and 0 <= y + dy < n and \
                            (x + dx, y + dy) not in seen and \
                            board[x + dx][y + dy] == 'O':
                        nq.append((x + dx, y + dy))
                        seen.add((x + dx, y + dy))
                if not q:
                    q, nq = nq, q
            if not hasBorder:
                for x, y in region:
                    board[x][y] = 'X'

        for i, j in os:
            if (i, j) not in seen:
                bfs(i, j, seen)


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        board = [["X", "O", "X"], ["O", "X", "O"], ["X", "O", "X"]]
        sol.solve(board)
        self.assertEqual([["X", "O", "X"], ["O", "X", "O"], ["X", "O", "X"]], board)

    def testSample2(self):
        sol = Solution()
        board = [["X", "X", "X", "X"], ["X", "O", "O", "X"], ["X", "X", "O", "X"], ["X", "O", "X", "X"]]
        sol.solve(board)
        self.assertEqual([["X", "X", "X", "X"], ["X", "X", "X", "X"], ["X", "X", "X", "X"], ["X", "O", "X", "X"]], board)