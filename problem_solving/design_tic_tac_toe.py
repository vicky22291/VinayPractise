"""
URL: https://leetcode.com/problems/design-tic-tac-toe/?envType=company&envId=databricks&favoriteSlug=databricks-all

9 * 9
mins = {
    rows = [] * n
    cols = [] * n
    diag1 = 1
    diag2 = 1
}
maxs = {
    rows = [] * n
    cols = [] * n
    diag1 = 1
    diag2 = 1
}
Space 4n -- O(n)
Time O(1)

0 0
0 0

0 0 0
0 0 0
0 0 0

"""
from typing import List


class TicTacToe:

    @staticmethod
    def _get_defaults(n: int, val: int):
        return [
            [val] * n,
            [val] * n,
            [val],
            [val]
        ]

    def __init__(self, n: int):
        self.mins = TicTacToe._get_defaults(n, 3)
        self.maxs = TicTacToe._get_defaults(n, 0)
        self.counts = TicTacToe._get_defaults(n, 0)
        self.n = n

    def _identify_loc(self, row: int, col: int):
        ans = [[0, row], [1, col]]
        if row == col:
            ans.append([2, 0])
        if row + col == (self.n - 1):
            ans.append([3, 0])
        return ans

    def move(self, row: int, col: int, player: int) -> int:
        for i, j in self._identify_loc(row, col):
            self.mins[i][j] = min(self.mins[i][j], player)
            self.maxs[i][j] = max(self.maxs[i][j], player)
            self.counts[i][j] += 1
            if self.counts[i][j] == self.n and self.mins[i][j] == self.maxs[i][j]:
                return self.mins[i][j]
        return 0


def run(n: int, moves: List[int]):
    sol = TicTacToe(n)
    for r, c, p in moves:
        print(sol.move(r, c, p))

run(3, [[0,0,1],[0,2,2],[2,2,1],[1,1,2],[2,0,1],[1,0,2],[2,1,1]])