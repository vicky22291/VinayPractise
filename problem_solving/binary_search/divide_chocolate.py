"""
    https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/710/binary-search/4681/
"""
import unittest
from typing import List


class Solution:
    def maximizeSweetness(self, sweetness: List[int], k: int) -> int:
        number_of_people = k + 1
        left = min(sweetness)
        right = sum(sweetness) // number_of_people

        while left < right:
            mid = (left + right + 1) // 2
            cur_sweetness = 0
            people_with_chocolate = 0

            for s in sweetness:
                cur_sweetness += s

                if cur_sweetness >= mid:
                    people_with_chocolate += 1
                    cur_sweetness = 0

            if people_with_chocolate >= k + 1:
                left = mid
            else:
                right = mid - 1

        return right


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(6, sol.maximizeSweetness([1, 2, 3, 4, 5, 6, 7, 8, 9], 5))

    def testSample2(self):
        sol = Solution()
        self.assertEqual(1, sol.maximizeSweetness([5, 6, 7, 8, 9, 1, 2, 3, 4], 8))
