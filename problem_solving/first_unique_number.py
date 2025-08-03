"""
URL: https://leetcode.com/problems/first-unique-number
"""
from collections import deque
from typing import List


class FirstUnique:

    def __init__(self, nums: List[int]):
        self._queue = deque(nums)
        self._is_unique = {}
        for num in nums:
            self.add(num)

    def showFirstUnique(self) -> int:
        while self._queue and not self._is_unique[self._queue[0]]:
            self._queue.popleft()
        if self._queue:
            return self._queue[0]
        return -1

    def add(self, value: int) -> None:
        if value not in self._is_unique:
            self._is_unique[value] = True
            self._queue.append(value)
        else:
            self._is_unique[value] = False

sol = FirstUnique([2,3,5])
print(sol.showFirstUnique())
print(sol.add(5))
print(sol.showFirstUnique())
print(sol.add(2))
print(sol.showFirstUnique())
print(sol.add(3))
print(sol.showFirstUnique())