import unittest
from typing import List


class Solution:
    def longestLine(self, mat: List[List[int]]) -> int:
        m, n = len(mat), len(mat[0])
        ans = 0

        def bfs(i, j):
            nonlocal ans, mat
            q, nq = [], []
            count = 0

            for orient in ['V', 'H', 'D', 'AD']:
                next = (i, j, orient)
                if next not in seen:
                    q.append(next)
            while q:
                r, c, orient = q.pop()
                if orient == 'V' and r < m - 1:
                    next = (r + 1, c, orient)
                elif orient == 'H' and c < n - 1:
                    next = (r, c + 1, orient)
                elif orient == 'D' and r < m - 1 and c < n - 1:
                    next = (r + 1, c + 1, orient)
                elif orient == 'AD' and r < m - 1 and c > 0:
                    next = (r + 1, c - 1, orient)
                else:
                    next = None
                if next and next not in seen and mat[next[0]][next[1]]:
                    nq.append(next)
                    seen.add(next)
                if not q:
                    q, nq = nq, q
                    count += 1
            ans = max(ans, count)

        seen = set()
        for i in range(m):
            for j in range(n):
                if mat[i][j]:
                    bfs(i, j)
        return ans


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(9, sol.longestLine(
            [[1, 1, 0, 0, 1, 0, 0, 1, 1, 0], [1, 0, 0, 1, 0, 1, 1, 1, 1, 1], [1, 1, 1, 0, 0, 1, 1, 1, 1, 0],
             [0, 1, 1, 1, 0, 1, 1, 1, 1, 1], [0, 0, 1, 1, 1, 1, 1, 1, 1, 0], [1, 1, 1, 1, 1, 1, 0, 1, 1, 1],
             [0, 1, 1, 1, 1, 1, 1, 0, 0, 1], [1, 1, 1, 1, 1, 0, 0, 1, 1, 1], [0, 1, 0, 1, 1, 0, 1, 1, 1, 1],
             [1, 1, 1, 0, 1, 0, 1, 1, 1, 1]]))
