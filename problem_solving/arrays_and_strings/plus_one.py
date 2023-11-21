"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/92/array/559/
"""
import collections
from typing import List


class Solution:
    def plusOne(self, digits: List[int]) -> List[int]:
        ans = collections.deque()
        carry = 0
        for digit in digits[::-1]:
            ans.appendleft((carry + digit) % 10)
            carry = (carry + digit) // 10
        if carry:
            ans.appendleft(carry)
        return ans