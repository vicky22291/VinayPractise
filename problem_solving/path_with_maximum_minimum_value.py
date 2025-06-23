"""
URL: https://leetcode.com/problems/path-with-maximum-minimum-value/description
"""
import heapq
from typing import List


class Solution:
    def maximumMinimumPath(self, grid: List[List[int]]) -> int:
        """
        m, n = len(grid), len(grid[0])
        seen = set()

        def nextStep(x, y):
            nonlocal m, n, seen
            res = []
            maxValue = None
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                if (x + dx, y + dy) not in seen and 0 <= x + dx < m and 0 <= y + dy < n:
                    if maxValue is None or maxValue < grid[x + dx][y + dy]:
                        maxValue = grid[x + dx][y + dy]
                        res = [(x + dx, y + dy)]
                    elif maxValue == grid[x + dx][y + dy]:
                        res.append((x + dx, y + dy))
            return res

        def minValue(x, y, min_so_far):
            seen.add((x, y))
            if x == m - 1 and y == n - 1:
                seen.remove((x, y))
                return min(min_so_far, grid[x][y])
            maxValue = -1_000_000_000
            for nx, ny in nextStep(x, y):
                maxValue = max(maxValue, minValue(nx, ny, min(grid[x][y], min_so_far)))
            seen.remove((x, y))
            return min(grid[x][y], maxValue)

        return minValue(0, 0, grid[0][0])
        """
        R = len(grid)
        C = len(grid[0])

        # 4 directions to a cell's possible neighbors.
        dirs = [(1, 0), (0, 1), (-1, 0), (0, -1)]

        heap = []
        ans = grid[0][0]

        # Initalize the status of all the cells as 0 (unvisited).
        visited = [[False] * C for _ in range(R)]

        # Put the top-left cell to the priority queue and mark it as True (visited).
        # Notice that we save the negative number of cell's value, thus we can always
        # pop out the cell with the maximum value using a min-heap data structure.
        heapq.heappush(heap, (-grid[0][0], 0, 0))
        visited[0][0] = True

        # While the priority queue is not empty.
        while heap:
            # Pop the cell with the largest value.
            cur_val, cur_row, cur_col = heapq.heappop(heap)

            # Update the minimum value we have visited so far.
            ans = min(ans, grid[cur_row][cur_col])

            # If we reach the bottom-right cell, stop the iteration.
            if cur_row == R - 1 and cur_col == C - 1:
                break
            for d_row, d_col in dirs:
                new_row = cur_row + d_row
                new_col = cur_col + d_col

                # Check if the current cell has any unvisited neighbors.
                if (
                    0 <= new_row < R
                    and 0 <= new_col < C
                    and not visited[new_row][new_col]
                ):
                    # If so, we put this neighbor to the priority queue
                    # and mark it as True (visited).
                    heapq.heappush(
                        heap, (-grid[new_row][new_col], new_row, new_col)
                    )
                    visited[new_row][new_col] = True

        # Return the minimum value we have seen, which is the value of this path.
        return ans