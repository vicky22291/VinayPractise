"""
URL: https://leetcode.com/problems/car-pooling
"""
from heapq import heappop, heappush
from typing import List


class Solution:
    def carPooling(self, trips: List[List[int]], capacity: int) -> bool:
        hp, car = [], 0
        trips = sorted(trips, key=lambda x: x[1])
        for n, s, e in trips:
            while len(hp) and hp[0][0] <= s:
                pe, pn = heappop(hp)
                car -= pn
            car += n
            heappush(hp, [e, n])
            if car > capacity:
                return False
        return True