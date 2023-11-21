"""
    https://leetcode.com/explore/interview/card/top-interview-questions-hard/116/array-and-strings/830/
"""
from typing import List


class Solution(object):
    def maxArea(self, height: List[int]) -> int:
        left, right = 0, len(height) - 1
        maxArea = 0
        while left < right:
            maxArea = max(maxArea, min(height[left], height[right]) * (right - left))
            if height[left] < height[right]:
                left += 1
            else:
                right -= 1
        return maxArea