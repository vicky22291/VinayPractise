"""
URL: https://leetcode.com/problems/number-of-islands/description/

Given an m x n 2D binary grid grid which represents a map of '1's (land) and '0's (water), return the number of islands.

An island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically. You may assume all four edges of the grid are all surrounded by water.



Example 1:

Input: grid = [
  ["1","1","1","1","0"],
  ["1","1","0","1","0"],
  ["1","1","0","0","0"],
  ["0","0","0","0","0"]
]
Output: 1
Example 2:

Input: grid = [
  ["1","1","0","0","0"],
  ["1","1","0","0","0"],
  ["0","0","1","0","0"],
  ["0","0","0","1","1"]
]
Output: 3


Constraints:

m == grid.length
n == grid[i].length
1 <= m, n <= 300
grid[i][j] is '0' or '1'.
"""
from typing import List


class Solution:
    def numIslands(self, grid: List[List[str]]) -> int:
        num_of_islands = 0
        m = len(grid)
        n = len(grid[0])
        def get_neighbors(r, c):
            ans = []
            for ir, ic in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = r + ir, c + ic
                if 0 <= nr < m and 0 <= nc < n:
                    ans.append((nr, nc))
            return ans
        def dfs(r, c):
            if grid[r][c] == '1':
                grid[r][c] = -1
                for nr, nc in get_neighbors(r, c):
                    dfs(nr, nc)
        for i in range(m):
            for j in range(n):
                if grid[i][j] == '1':
                    dfs(i, j)
                    num_of_islands += 1
        return num_of_islands