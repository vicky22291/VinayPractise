"""
URL: https://leetcode.com/problems/maximum-product-of-two-digits/description
"""
from collections import Counter


class Solution:
    def maxProduct(self, n: int) -> int:
        digits = Counter(str(n))
        first = None
        for digit in "9876543210":
            if digit in digits:
                if first is None:
                    if digits[digit] >= 2:
                        return int(digit) ** 2
                    else:
                        first = int(digit)
                else:
                    return int(digit) * first
        return -1