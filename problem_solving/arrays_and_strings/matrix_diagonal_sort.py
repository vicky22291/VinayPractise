"""
    https://leetcode.com/problems/sort-the-matrix-diagonally/
"""
from typing import List


class Solution:
    def diagonalSort(self, mat: List[List[int]]) -> List[List[int]]:
        m, n = len(mat), len(mat[0])
        for i in range(n):
            data = []
            r = 0
            j = i
            while 0 <= r < m and 0 <= j < n:
                data.append(mat[r][j])
                r += 1
                j += 1
            data = sorted(data)
            r = 0
            j = i
            index = 0
            while 0 <= r < m and 0 <= j < n:
                mat[r][j] = data[index]
                r += 1
                j += 1
                index += 1
        for i in range(1, m):
            data = []
            r = i
            j = 0
            while 0 <= r < m and 0 <= j < n:
                data.append(mat[r][j])
                r += 1
                j += 1
            data = sorted(data)
            r = i
            j = 0
            index = 0
            while 0 <= r < m and 0 <= j < n:
                mat[r][j] = data[index]
                r += 1
                j += 1
                index += 1
        return mat