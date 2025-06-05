"""
URL: https://leetcode.com/problems/random-pick-index
"""
from bisect import bisect_left, bisect_right
from random import randint
from typing import List


class Solution:

    def __init__(self, nums: List[int]):
        self.nums = sorted([(i, num) for i, num in enumerate(nums)], key=lambda x: x[1])

    def pick(self, target: int) -> int:
        left = bisect_left(self.nums, target, key=lambda x: x[1])
        right = bisect_right(self.nums, target, key=lambda x: x[1]) - 1
        return self.nums[randint(left, right)][0]

# Your Solution object will be instantiated and called as such:
# obj = Solution(nums)
# param_1 = obj.pick(target)