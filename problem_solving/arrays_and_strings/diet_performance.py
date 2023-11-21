import collections
import unittest
from typing import List


class Solution:
    def dietPlanPerformance(self, calories: List[int], k: int, lower: int, upper: int) -> int:
        def returnPoints(calorie):
            if calorie > upper:
                return 1
            elif calorie < lower:
                return -1
            else:
                return 0

        window = collections.deque()
        for calorie in calories[:k]:
            window.append(calorie)
        curSum = sum(window)
        points = returnPoints(curSum)
        if k < len(calories):
            for calorie in calories[k:]:
                curSum += -window.popleft() + calorie
                window.append(calorie)
                points += returnPoints(curSum)
        return points


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(0, sol.dietPlanPerformance([1, 2, 3, 4, 5], 1, 3, 3))
