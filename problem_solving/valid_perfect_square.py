"""
URL: https://leetcode.com/problems/valid-perfect-square
"""
class Solution:
    def isPerfectSquare(self, num: int) -> bool:
        left, right = 0, num
        while left <= right:
            mid = (left + right) // 2
            mid_2 = mid ** 2
            if mid_2 > num:
                right = mid - 1
            elif mid_2 < num:
                left = mid + 1
            else:
                return True
        return False