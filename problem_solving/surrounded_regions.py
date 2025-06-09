"""
URL: https://leetcode.com/problems/surrounded-regions/
"""
from typing import List


class Solution:
    def solve(self, board: List[List[str]]) -> None:
        """
        Do not return anything, modify board in-place instead.
        """
        """
        seen, to_be_seen, m, n = set(), set(), len(board), len(board[0])
        for i in range(m):
            for j in range(n):
                if board[i][j] == 'O':
                    to_be_seen.add((i, j))

        def dfs(i, j, cur):
            nonlocal seen, m, n
            seen.add((i, j))
            cur.add((i, j))
            hasEdge = False
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                if 0 <= i + dr < m and 0 <= j + dc < n and (i + dr, j + dc) not in seen and board[i + dr][
                    j + dc] == "O":
                    hasEdge = hasEdge or dfs(i + dr, j + dc, cur)
            return i == 0 or i == (m - 1) or j == 0 or j == (n - 1) or hasEdge

        while len(to_be_seen):
            for x, y in to_be_seen:
                cur = set()
                if not dfs(x, y, cur):
                    for i, j in cur:
                        board[i][j] = 'X'
                break
            to_be_seen = to_be_seen - seen
        """
        if not board or not board[0]:
            return

        self.ROWS = len(board)
        self.COLS = len(board[0])

        # Step 1). retrieve all border cells
        from itertools import product

        borders = list(product(range(self.ROWS), [0, self.COLS - 1])) + list(
            product([0, self.ROWS - 1], range(self.COLS))
        )

        # Step 2). mark the "escaped" cells, with any placeholder, e.g. 'E'
        for row, col in borders:
            self.BFS(board, row, col)

        # Step 3). flip the captured cells ('O'->'X') and the escaped one ('E'->'O')
        for r in range(self.ROWS):
            for c in range(self.COLS):
                if board[r][c] == "O":
                    board[r][c] = "X"  # captured
                elif board[r][c] == "E":
                    board[r][c] = "O"  # escaped

    def BFS(self, board: List[List[str]], row: int, col: int) -> None:
        from collections import deque

        queue = deque([(row, col)])
        while queue:
            (row, col) = queue.popleft()
            if board[row][col] != "O":
                continue
            # mark this cell as escaped
            board[row][col] = "E"
            # check its neighbor cells
            if col < self.COLS - 1:
                queue.append((row, col + 1))
            if row < self.ROWS - 1:
                queue.append((row + 1, col))
            if col > 0:
                queue.append((row, col - 1))
            if row > 0:
                queue.append((row - 1, col))


sol = Solution()
print(sol.solve([["X","O","X"],["O","X","O"],["X","O","X"]]))