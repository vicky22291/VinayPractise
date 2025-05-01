"""
URL: https://leetcode.com/problems/minimum-knight-moves/

In an infinite chess board with coordinates from -infinity to +infinity, you have a knight at square [0, 0].

A knight has 8 possible moves it can make, as illustrated below. Each move is two squares in a cardinal direction, then one square in an orthogonal direction.


Return the minimum number of steps needed to move the knight to the square [x, y]. It is guaranteed the answer exists.



Example 1:

Input: x = 2, y = 1
Output: 1
Explanation: [0, 0] → [2, 1]
Example 2:

Input: x = 5, y = 5
Output: 4
Explanation: [0, 0] → [2, 1] → [4, 2] → [3, 4] → [5, 5]


Constraints:

-300 <= x, y <= 300
0 <= |x| + |y| <= 300
"""
from functools import lru_cache


class Solution:
    def minKnightMoves(self, x: int, y: int) -> int:
        queue, next_queue, moves, visited, m, n = [(0, 0)], [], 0, set(), 8, 8
        while len(queue):
            r, c = queue.pop()
            if (r, c) == (x, y):
                return moves
            visited.add((r, c))
            for ir, ic in [(2, 1), (-2, -1), (2, -1), (-2, 1), (1, 2), (-1, -2), (-1, 2), (1, -2)]:
                nr, nc = r + ir, c + ic
                if (nr, nc) not in visited:
                    next_queue.append((nr, nc))
            if len(queue) == 0:
                queue, next_queue = next_queue, queue
                moves += 1
        return moves

class Solution2:
    def minKnightMoves(self, x: int, y: int) -> int:

        @lru_cache(maxsize=None)
        def dfs(x, y):
            if x + y == 0:
                # base case: (0, 0)
                return 0
            elif x + y == 2:
                # base case: (1, 1), (0, 2), (2, 0)
                return 2
            else:
                return min(dfs(abs(x - 1), abs(y - 2)), dfs(abs(x - 2), abs(y - 1))) + 1

        return dfs(abs(x), abs(y))

sol = Solution()
print(sol.minKnightMoves(1, 1))