"""
URL: https://leetcode.com/problems/reverse-integer/description/

Given a signed 32-bit integer x, return x with its digits reversed. If reversing x causes the value to go outside the signed 32-bit integer range [-231, 231 - 1], then return 0.

Assume the environment does not allow you to store 64-bit integers (signed or unsigned).



Example 1:

Input: x = 123
Output: 321
Example 2:

Input: x = -123
Output: -321
Example 3:

Input: x = 120
Output: 21


Constraints:

-231 <= x <= 231 - 1
"""


class Solution:
    def reverse(self, x: int) -> int:
        isNeg = x < 0
        x = abs(x)
        digits = []
        while x:
            if len(digits) != 0 or x % 10 != 0:
                digits.append(str(x % 10))
            x //= 10
        if len(digits) == 0:
            return 0
        reversed_x_str = "".join(digits)
        if len(digits) < 10:
            return int(reversed_x_str) * (-1 if isNeg else 1)
        else:
            if (isNeg and reversed_x_str > "2147483648") or (not isNeg and reversed_x_str > "2147483647"):
                return 0
            else:
                return int(reversed_x_str) * (-1 if isNeg else 1)
