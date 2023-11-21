"""
    https://leetcode.com/problems/number-of-steps-to-reduce-a-number-to-zero/description/
"""


class Solution:
    def numberOfSteps(self, num: int) -> int:
        steps = 0
        while num:
            if num & 1:
                num -= 1
            else:
                num >>= 1
            steps += 1
        return steps
