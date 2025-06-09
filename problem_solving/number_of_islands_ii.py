"""
URL: https://leetcode.com/problems/number-of-islands-ii/description
"""
from typing import List


class UnionFind:
    def __init__(self, size):
        self.count = 0
        self.parent = [-1] * size
        self.rank = [0] * size

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        rootx = self.find(x)
        rooty = self.find(y)
        if rootx != rooty:
            if self.rank[rootx] < self.rank[rooty]:
                self.parent[rootx] = rooty
            elif self.rank[rootx] > self.rank[rooty]:
                self.parent[rooty] = rootx
            else:
                self.parent[rootx] = rooty
                self.rank[rooty] += 1
            self.count -= 1

    def add(self, x):
        if self.parent[x] == -1:
            self.parent[x] = x
            self.count += 1

    def getCount(self):
        return self.count

class Solution:
    def numIslands2(self, m: int, n: int, positions: List[List[int]]) -> List[int]:
        """
        grid = [[0] * n for _ in range(m)]
        parents = set()
        links = {}
        ans = []
        nIslands = 0

        def getParents(i, j):
            nonlocal links
            while (i, j) in links:
                i, j = links[(i, j)]
            return i, j

        for x, y in positions:
            grid[x][y] = 1
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                if 0 <= x + dr < m and 0 <= y + dc < n and grid[x + dr][y + dc]:
                    if (x, y) not in links:
                        if (x + dr, y + dc) in parents:
                            links[(x, y)] = (x + dr, y + dc)
                        elif (x + dr, y + dc) in links:
                            links[(x, y)] = links[(x + dr, y + dc)]
                    else:
                        px, py = getParents(x, y)
                        pnx, pny = getParents(x + dr, y + dc)
                        if pnx != px or pny != py:
                            parents.remove((px, py))
                            links[(px, py)] = pnx, pny
                            nIslands -= 1
            if (x, y) not in links:
                parents.add((x, y))
                nIslands += 1
            ans.append(nIslands)
        return ans
        """
        # Time: O(k * alpha(m*n)), Space: O(m * n)
        # k = number of land additions, alpha = inverse Ackermann function
        def valid(r, c):
            return 0 <= r < m and 0 <= c < n and uf.parent[r*n+c] != -1

        uf = UnionFind(m * n)
        directions = [[-1,0],[1,0],[0,-1],[0,1]]
        res = []

        for r, c in positions:
            idx = r * n + c
            uf.add(idx)
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if valid(nr, nc):
                    uf.union(idx, nr * n + nc)
            res.append(uf.getCount())
        return res


sol = Solution()
print(sol.numIslands2(3, 3, [[0,1],[1,2],[2,1],[1,0],[0,2],[0,0],[1,1]]))