import heapq
import unittest
from typing import List


class Solution:
    def cutOffTree(self, forest: List[List[int]]) -> int:
        m, n = len(forest), len(forest[0])
        trees = []
        for i in range(m):
            for j in range(n):
                if forest[i][j] > 1:
                    trees.append((forest[i][j], i, j))
        trees.sort()

        def bfs(sx, sy, tx, ty):
            queue = [(0, sx, sy)]
            visited = set()
            visited.add((sx, sy))
            while queue:
                d, x, y = heapq.heappop(queue)
                if x == tx and y == ty:
                    return d
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < m and 0 <= ny < n and (nx, ny) not in visited and forest[nx][ny]:
                        visited.add((nx, ny))
                        heapq.heappush(queue, (d + 1, nx, ny))
            return -1

        ans = 0
        sx, sy = 0, 0
        for _, tx, ty in trees:
            d = bfs(sx, sy, tx, ty)
            if d == -1:
                return -1
            ans += d
            sx, sy = tx, ty
        return ans


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(6, sol.cutOffTree([[1, 2, 3], [0, 0, 4], [7, 6, 5]]))

    def testSample2(self):
        sol = Solution()
        self.assertEqual(57, sol.cutOffTree(
            [[54581641, 64080174, 24346381, 69107959], [86374198, 61363882, 68783324, 79706116],
             [668150, 92178815, 89819108, 94701471], [83920491, 22724204, 46281641, 47531096],
             [89078499, 18904913, 25462145, 60813308]]))
