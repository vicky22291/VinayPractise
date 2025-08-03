"""
URL: https://leetcode.com/problems/the-maze-ii/description
"""
from typing import List


class Solution:
    def shortestDistance(self, maze: List[List[int]], start: List[int], destination: List[int]) -> int:
        if (start[0], start[1]) == (destination[0], destination[1]):
            return 0
        q, nQ, m, n = [(start, None)], [], len(maze), len(maze[0])
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        seen = set()
        seen.add(((start[0], start[1]), None))
        dist = 0
        while len(q):
            point, dir = q.pop()
            x, y = point
            searchForOtherDirections = True
            if dir:
                dx, dy = dir
                if ((x, y) == (destination[0], destination[1]) and
                        not (0 <= x + dx < m and 0 <= y + dy < n and maze[x + dx][y + dy] != 1)):
                    return dist
                if 0 <= x + dx < m and 0 <= y + dy < n and maze[x + dx][y + dy] != 1:
                    nQ.append(((x + dx, y + dy), (dx, dy)))
                    searchForOtherDirections = False
            if searchForOtherDirections:
                for dx, dy in directions:
                    if ((dx, dy) != dir and
                            0 <= x + dx < m and 0 <= y + dy < n and
                            maze[x + dx][y + dy] != 1 and
                            ((x + dx, y + dy), (dx, dy)) not in seen):
                        nQ.append(((x + dx, y + dy), (dx, dy)))
                        seen.add(((x + dx, y + dy), (dx, dy)))
            if not len(q):
                q, nQ = nQ, q
                dist += 1
        return -1

sol = Solution()
print(sol.shortestDistance([[0,0,1,0,0],[0,0,0,0,0],[0,0,0,1,0],[1,1,0,1,1],[0,0,0,0,0]], [0, 4], [4, 4]))