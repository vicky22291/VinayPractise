"""
    https://leetcode.com/explore/interview/card/top-interview-questions-hard/116/array-and-strings/836/
"""
import unittest


class Solution:
    def calculate(self, s: str) -> int:
        operator_to_evaluate, curr_num, accu, result = '+', 0, 0, 0
        for c in s+'#':
            if c == ' ':
                continue
            elif c.isdigit():
                curr_num = curr_num*10 + int(c)
            else:
                if operator_to_evaluate == '+':
                    result += accu
                    accu = curr_num
                elif operator_to_evaluate == '-':
                    result += accu
                    accu = -curr_num
                elif operator_to_evaluate == '*':
                    accu = accu * curr_num
                elif operator_to_evaluate == '/':
                    accu = int(accu / curr_num)

                operator_to_evaluate = c
                curr_num = 0

                if c == '#':
                    result += accu
        return result


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(7, sol.calculate("3+2*2"))

    def testSample2(self):
        sol = Solution()
        self.assertEqual(20, sol.calculate("3+4+2*2*2+5"))