"""
URL: https://leetcode.com/problems/sparse-matrix-multiplication/description
"""
from typing import List


class Solution:
    def multiply(self, mat1: List[List[int]], mat2: List[List[int]]) -> List[List[int]]:
        m, k, n = len(mat1), len(mat1[0]), len(mat2[0])
        ans = []
        for i in range(m):
            ans.append([])
            for j in range(n):
                num = 0
                for mid in range(k):
                    num += mat1[i][mid] * mat2[mid][j]
                ans[-1].append(num)
        return ans