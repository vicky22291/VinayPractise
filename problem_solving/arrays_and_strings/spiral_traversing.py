"""
    https://leetcode.com/problems/spiral-matrix-ii/description/
"""


from typing import List


class Solution:
    def generateMatrix(self, n: int) -> List[List[int]]:
        grid = [[0] * n for _ in range(n)]
        x, y = 0, 0
        i = 1
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        di = 0
        while x < n and y < n and grid[x][y] == 0:
            grid[x][y] = i
            dx, dy = directions[di]
            if 0 <= x + dx < n and 0 <= y + dy < n and grid[x + dx][y + dy] == 0:
                x += dx
                y += dy
            else:
                di = (di + 1) % 4
                dx, dy = directions[di]
                x += dx
                y += dy
            i += 1
        return grid
