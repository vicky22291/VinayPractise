"""
URL: https://leetcode.com/problems/can-make-arithmetic-progression-from-sequence/
"""
from typing import List


class Solution:
    def canMakeArithmeticProgression(self, arr: List[int]) -> bool:
        sorted_arr = sorted(arr)
        diff = sorted_arr[1] - sorted_arr[0]
        for i in range(2, len(arr)):
            if diff != sorted_arr[i] - sorted_arr[i - 1]:
                return False
        return True