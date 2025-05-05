"""
URL: https://leetcode.com/problems/largest-rectangle-in-histogram/

Given an array of integers heights representing the histogram's bar height where the width of each bar is 1, return the area of the largest rectangle in the histogram.



Example 1:


Input: heights = [2,1,5,6,2,3]
Output: 10
Explanation: The above is a histogram where width of each bar is 1.
The largest rectangle is shown in the red area, which has an area = 10 units.
Example 2:


Input: heights = [2,4]
Output: 4


Constraints:

1 <= heights.length <= 105
0 <= heights[i] <= 104
"""
from typing import List


class Solution:
    def largestRectangleArea(self, heights: List[int]) -> int:
        stack, max_area, n = [-1], 0, len(heights)
        for i in range(n):
            while stack[-1] != -1 and heights[stack[-1]] >= heights[i]:
                popped = stack.pop()
                max_area = max(max_area, heights[popped] * (i - stack[-1] - 1))
            stack.append(i)

        while stack[-1] != -1:
            popped = stack.pop()
            max_area = max(max_area, heights[popped] * (n - stack[-1] - 1))

        return max_area