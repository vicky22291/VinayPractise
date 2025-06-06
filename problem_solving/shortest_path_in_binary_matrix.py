"""
URL: https://leetcode.com/problems/shortest-path-in-binary-matrix

Given an n x n binary matrix grid, return the length of the shortest clear path in the matrix. If there is no clear path, return -1.

A clear path in a binary matrix is a path from the top-left cell (i.e., (0, 0)) to the bottom-right cell (i.e., (n - 1, n - 1)) such that:

All the visited cells of the path are 0.
All the adjacent cells of the path are 8-directionally connected (i.e., they are different and they share an edge or a corner).
The length of a clear path is the number of visited cells of this path.



Example 1:


Input: grid = [[0,1],[1,0]]
Output: 2
Example 2:


Input: grid = [[0,0,0],[1,1,0],[1,1,0]]
Output: 4
Example 3:

Input: grid = [[1,0,0],[1,1,0],[1,1,0]]
Output: -1


Constraints:

n == grid.length
n == grid[i].length
1 <= n <= 100
grid[i][j] is 0 or 1
"""
from typing import List


class Solution:
    def shortestPathBinaryMatrix(self, grid: List[List[int]]) -> int:
        n = len(grid)
        if grid[n - 1][n - 1] == 1:
            return -1
        elif grid[0][0] == 1:
            return -1
        elif n == 1:
            return 1
        queue, next_queue, count = [(0, 0)], [], 1
        while len(queue):
            r, c = queue.pop()
            if grid[r][c] == 0:
                grid[r][c] = -1
                for ir, ic in [(1, 1), (1, 0), (0, 1), (0, -1), (-1, 0), (-1, -1), (1, -1), (-1, 1)]:
                    if 0 <= r + ir < n and 0 <= c + ic < n and grid[r + ir][c + ic] == 0:
                        if r + ir == n - 1 and c + ic == n - 1:
                            return count + 1
                        next_queue.append((r + ir, c + ic))
            if len(queue) == 0:
                queue, next_queue = next_queue, queue
                count += 1
        return -1


