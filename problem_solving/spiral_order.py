"""
URL: https://leetcode.com/problems/spiral-matrix/

Given an m x n matrix, return all elements of the matrix in spiral order.



Example 1:


Input: matrix = [[1,2,3],[4,5,6],[7,8,9]]
Output: [1,2,3,6,9,8,7,4,5]
Example 2:


Input: matrix = [[1,2,3,4],[5,6,7,8],[9,10,11,12]]
Output: [1,2,3,4,8,12,11,10,9,5,6,7]


Constraints:

m == matrix.length
n == matrix[i].length
1 <= m, n <= 10
-100 <= matrix[i][j] <= 100
"""
from typing import List


class Solution:
    def spiralOrder(self, matrix: List[List[int]]) -> List[int]:
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        increments = [(1, 0, 0, 0), (0, 0, 0, -1), (0, -1, 0, 0), (0, 0, 1, 0)]
        m, n = len(matrix), len(matrix[-1])
        rs, re, cs, ce = 0, m - 1, 0, n - 1
        ref = i = j = dr = dc = 0
        result = []
        while rs <= re and cs <= ce:
            if not (rs <= i <= re and cs <= j <= ce):
                irs, ire, ics, ice = increments[ref % 4]
                rs, re, cs, ce = rs + irs, re + ire, cs + ics, ce + ice
                ref += 1
                ## Coming back to the last correct location.
                i, j = i - dr, j - dc
                ## Getting new directions
                dr, dc = directions[ref % 4]
                ## Updating location based on new direction.
                i, j = i + dr, j + dc
            if rs <= i <= re and cs <= j <= ce:
                result.append(matrix[i][j])
                dr, dc = directions[ref % 4]
                i, j = i + dr, j + dc
        return result

sol = Solution()
print(sol.spiralOrder([[1,2,3],[4,5,6],[7,8,9]]))
print(sol.spiralOrder([[1,2,3,4],[5,6,7,8],[9,10,11,12]]))