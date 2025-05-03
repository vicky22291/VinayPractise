"""
URL: https://leetcode.com/problems/search-a-2d-matrix/description/

You are given an m x n integer matrix matrix with the following two properties:

Each row is sorted in non-decreasing order.
The first integer of each row is greater than the last integer of the previous row.
Given an integer target, return true if target is in matrix or false otherwise.

You must write a solution in O(log(m * n)) time complexity.



Example 1:


Input: matrix = [[1,3,5,7],[10,11,16,20],[23,30,34,60]], target = 3
Output: true
Example 2:


Input: matrix = [[1,3,5,7],[10,11,16,20],[23,30,34,60]], target = 13
Output: false


Constraints:

m == matrix.length
n == matrix[i].length
1 <= m, n <= 100
-104 <= matrix[i][j], target <= 104
"""
from bisect import bisect_right
from typing import List


class Solution:
    def searchMatrix(self, matrix: List[List[int]], target: int) -> bool:
        last_col_values, m, n = [row[-1] for row in matrix], len(matrix), len(matrix[0])
        index = bisect_right(last_col_values, target)
        if last_col_values[index - 1] == target:
            return True
        elif index == m:
            return False
        row_index = bisect_right(matrix[index], target)
        if row_index == n:
            return False
        return matrix[index][row_index - 1] == target