"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/99/others/762/
"""
import unittest


class Solution:
    def hammingDistance(self, x: int, y: int) -> int:
        dist = 0
        while x or y:
            if y and not x:
                if y & 1:
                    dist += 1
                y >>= 1
            elif x and not y:
                if x & 1:
                    dist += 1
                x >>= 1
            else:
                if x & 1 or y & 1:
                    dist += int(x & 1 != y & 1)
                x >>= 1
                y >>= 1
        return dist


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(2, sol.hammingDistance(1, 4))