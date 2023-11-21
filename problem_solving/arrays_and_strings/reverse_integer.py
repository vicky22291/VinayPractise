import unittest


class Solution:
    def reverse(self, x: int) -> int:
        negativeSign = x < 0
        ans = int(str(abs(x))[::-1])
        if negativeSign and ans > 2 ** 31 or (not negativeSign and ans > (2 ** 31 - 1)):
            return 0
        else:
            return (-1 if negativeSign else 1) * ans


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(321, sol.reverse(123))