"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/102/math/744/
"""
from math import sqrt


class Solution:
    def countPrimes(self, n: int) -> int:
        """
        ans = []
        for i in range(2, n):
            isPrime = True
            for prime in ans:
                if i % prime == 0:
                    isPrime = False
                    break
            if isPrime:
                ans.append(i)
        return len(ans)
        if n <= 2:
            return 0
        """
        numbers = [False, False] + [True] * (n - 2)
        for p in range(2, int(sqrt(n)) + 1):
            if numbers[p]:
                for multiple in range(p * p, n, p):
                    numbers[multiple] = False
        return sum(numbers)