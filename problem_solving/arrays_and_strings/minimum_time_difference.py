"""
    https://leetcode.com/problems/minimum-time-difference/
"""
import unittest
from typing import List


class Solution:
    def findMinDifference(self, timePoints: List[str]) -> int:
        """
        def diffMins(time1, time2):
            if time1 == time2:
                return 0
            elif time1 > time2:
                return diffMins(time1, '23:59') + 1 + diffMins('00:00', time2)
            else:
                h1, m1 = time1.split(':')
                h2, m2 = time2.split(':')
                return (int(h2) - int(h1)) * 60 + (int(m2) - int(m1))

        prev = timePoints[0]
        minimum = 2000
        for time in timePoints[1:]:
            minimum = min(minimum, diffMins(prev, time))
            prev = time
        return minimum
        """
        def convert(time):
            h = int(time[:2])
            m = int(time[3:])
            return h * 60 + m

        l = [convert(t) for t in timePoints]
        l.sort()
        n = len(l)

        res = min(l[i + 1] - l[i] for i in range(n - 1))

        return min(res, 1440 - l[-1] + l[0])  # Think in anticlockwise


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(1, sol.findMinDifference(["23:59", "00:00"]))
