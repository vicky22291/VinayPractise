"""
    https://leetcode.com/explore/learn/card/dynamic-programming/631/strategy-for-solving-dp-problems/4046/

    How we structure the problem is:
    1. State Variables:
        row and column traversed so far. So the last value is the final answer.
    2. Recurrence Relationship:
        1. If value at i, j == 1 then only we can have a square.
        2. Considering other 3 matrices {(i - 1, j), (i, j - 1), (i - 1, j -1)}
        3. If the value at any of 3 points is zero then we will not have square numbers. Hence, if there are values then all 3 are 1s.
        4. (i - 1, j - 1) will be overlapped in (i - 1, j) and (i, j - 1)
        5. Similarly there will be overlap between (i - 1, j) and (i, j - 1)
        6. We need to consider only overlap so that we would not have zeroes in the square.
        7. So first we get the overlap by assuming the square towards the border is min. Hence, we would take min((i - 1, j) and (i, j - 1))
        8. The above should overlap with (i - 1, j - 1), so min((i - 1, j - 1), min((i - 1, j) and (i, j - 1)))
        9. Adding the current square value.
        10. final recurrence relationship is "dp(i, j)=min(dp(i−1, j), dp(i−1, j−1), dp(i, j−1))+1"
    3. We need to respond m, n
"""
from typing import List


class Solution:
    def maximalSquare(self, matrix: List[List[str]]) -> int:
        # Get the dimensions of the matrix
        m, n = len(matrix), len(matrix[0])

        # Initialize the dp array
        dp = [[0] * n for _ in range(m)]

        # Initialize the max size of the square seen so far
        max_size = 0

        # Fill the dp array
        for i in range(m):
            for j in range(n):
                if matrix[i][j] == '1':
                    if i == 0 or j == 0:
                        # First row or column, so the maximum size of the square is 1
                        dp[i][j] = 1
                    else:
                        # Check the values of the cells to the left, top, and top-left of the current cell
                        dp[i][j] = min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]) + 1

                    # Update the max size of the square seen so far
                    max_size = max(max_size, dp[i][j])

        # Return the area of the largest square
        return max_size * max_size