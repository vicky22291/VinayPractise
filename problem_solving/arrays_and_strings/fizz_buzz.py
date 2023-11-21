"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/102/math/743/
"""
from typing import List


class Solution:
    def fizzBuzz(self, n: int) -> List[str]:
        ans = ['' for _ in range(n)]
        for i in range(2, n, 3):
            ans[i] += 'Fizz'
        for i in range(4, n, 5):
            ans[i] += 'Buzz'
        for i in range(n):
            if ans[i] == '':
                ans[i] = str(i + 1)
        return ans