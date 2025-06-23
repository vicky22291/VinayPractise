"""
URL: https://leetcode.com/problems/boats-to-save-people/description
"""
from typing import List


class Solution:
    def numRescueBoats(self, people: List[int], limit: int) -> int:
        people.sort()
        l, r = 0, len(people) - 1
        n = 0
        while l <= r:
            if people[l] + people[r] <= limit or l == r:
                l += 1
                r -= 1
            else:
                r -= 1
            n += 1
        return n