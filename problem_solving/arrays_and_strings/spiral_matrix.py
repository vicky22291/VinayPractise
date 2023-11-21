"""
    https://leetcode.com/explore/interview/card/top-interview-questions-hard/116/array-and-strings/828/
"""
from typing import List


class Solution:
    def spiralOrder(self, matrix: List[List[int]]) -> List[int]:
        rows, columns = len(matrix), len(matrix[0])
        up = left = 0
        down = rows - 1
        right = columns - 1
        n = 0
        ans = []
        while n != rows * columns:
            for i in range(left, right + 1):
                ans.append(matrix[up][i])
                n += 1
            for i in range(up + 1, down + 1):
                ans.append(matrix[i][right])
                n += 1
            if up != down:
                for i in range(right - 1, left - 1, -1):
                    ans.append(matrix[down][i])
                    n += 1
            if left != right:
                for i in range(down - 1, up, -1):
                    ans.append(matrix[i][left])
                    n += 1
            up += 1
            left += 1
            right -= 1
            down -= 1
        return ans