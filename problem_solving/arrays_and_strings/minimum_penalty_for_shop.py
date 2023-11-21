"""
    https://leetcode.com/problems/minimum-penalty-for-a-shop/
"""
import unittest


class Solution:
    def bestClosingTime(self, customers: str) -> int:
        totalBusy = 0
        for char in customers:
            if char == 'Y':
                totalBusy += 1
        minHour = 0
        minimum = totalBusy
        prevBusy = 1 if customers[0] == 'Y' else 0
        for index in range(1, len(customers)):
            value = index + totalBusy - 2 * prevBusy
            if value < minimum:
                minimum, minHour = value, index
            prevBusy += 1 if customers[index] == 'Y' else 0
        if minimum > (len(customers) - totalBusy):
            return len(customers)
        else:
            return minHour


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(2, sol.bestClosingTime("YYNY"))

    def testSample2(self):
        sol = Solution()
        self.assertEqual(0, sol.bestClosingTime("NNNNN"))

    def testSample3(self):
        sol = Solution()
        self.assertEqual(4, sol.bestClosingTime("YYYY"))