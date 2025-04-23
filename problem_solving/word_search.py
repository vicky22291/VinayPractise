"""
URL: https://leetcode.com/problems/word-search/description/

Given an m x n grid of characters board and a string word, return true if word exists in the grid.

The word can be constructed from letters of sequentially adjacent cells, where adjacent cells are horizontally or vertically neighboring. The same letter cell may not be used more than once.



Example 1:


Input: board = [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], word = "ABCCED"
Output: true
Example 2:


Input: board = [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], word = "SEE"
Output: true
Example 3:


Input: board = [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], word = "ABCB"
Output: false


Constraints:

m == board.length
n = board[i].length
1 <= m, n <= 6
1 <= word.length <= 15
board and word consists of only lowercase and uppercase English letters.


Follow up: Could you use search pruning to make your solution faster with a larger board?
"""
from collections import defaultdict, Counter
from typing import List


class Solution:
    def exist(self, board: List[List[str]], word: str) -> bool:
        matrix_indexes, matrix_count, word_count, m, n = defaultdict(list), Counter(), Counter(word), len(board), len(
            board[0])
        for i, row in enumerate(board):
            for j, char in enumerate(row):
                matrix_count[char] += 1
                matrix_indexes[char].append((i, j))
        if len(word_count - matrix_count) != 0:
            return False

        def get_neighbors(r, c):
            result = []
            for ir, ic in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                if 0 <= r + ir < m and 0 <= c + ic < n:
                    result.append((r + ir, c + ic))
            return result

        visited = set()

        def dfs(r, c, wi):
            if wi == len(word):
                return True
            elif word[wi] != board[r][c]:
                return False
            elif wi + 1 == len(word):
                return True
            visited.add((r, c))
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in visited and dfs(nr, nc, wi + 1):
                    return True
            visited.remove((r, c))
            return False

        for r, c in matrix_indexes[word[0]]:
            if dfs(r, c, 0):
                return True
        return False

sol = Solution()
# print(sol.exist([["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], "ABCCED"))
# print(sol.exist([["a"]], "a"))
print(sol.exist([["A","B","C","E"],["S","F","E","S"],["A","D","E","E"]], "ABCESEEEFS"))