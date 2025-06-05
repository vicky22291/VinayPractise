"""
URL: https://leetcode.com/problems/shortest-path-in-a-hidden-grid
"""
from collections import deque


# """
# This is GridMaster's API interface.
# You should not implement it, or speculate about its implementation
# """
# class GridMaster(object):
#    def canMove(self, direction: str) -> bool:
#
#
#    def move(self, direction: str) -> None:
#
#
#    def isTarget(self) -> bool:
#
#

class Solution(object):
    def findShortestPath(self, master: 'GridMaster') -> int:
        target = None
        grid = set([(0, 0)])

        moves = {
            "R": (0, 1),
            "D": (1, 0),
            "L": (0, -1),
            "U": (-1, 0)
        }

        inv = {
            "R": "L",
            "D": "U",
            "L": "R",
            "U": "D"
        }

        def build_grid(r, c):

            nonlocal target
            nonlocal grid

            grid.add((r, c))

            if master.isTarget():
                target = (r, c)

            for dname, (dr, dc) in moves.items():
                nr = r + dr
                nc = c + dc

                if (nr, nc) not in grid and master.canMove(dname):
                    master.move(dname)
                    build_grid(nr, nc)
                    master.move(inv[dname])

        build_grid(0, 0)
        queue = deque([(0, 0, 0)])
        seen = set([(0, 0)])

        while queue:

            r, c, dist = queue.popleft()

            if (r, c) == target:
                return dist

            for dr, dc in moves.values():
                nr = r + dr
                nc = c + dc

                if (nr, nc) in grid and (nr, nc) not in seen:
                    queue.append((nr, nc, dist + 1))
                    seen.add((nr, nc))

        return -1