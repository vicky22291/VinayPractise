import unittest
from typing import List


class Solution:
    def binary_search(self, arr: List, target: int) -> int:
        left = 0
        right = len(arr)
        while left < right:
            mid = (left + right) // 2
            if arr[mid] > target:
                right = mid
            else:
                left = mid + 1

        return left - 1


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(3, sol.binary_search([1, 2, 2, 2, 3, 4, 5], 2))