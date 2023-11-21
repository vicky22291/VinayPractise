"""
    https://leetcode.com/problems/k-closest-points-to-origin/
"""
from typing import List


class Solution:
    def kClosest(self, points: List[List[int]], k: int) -> List[List[int]]:
        def getDistanceFromOrigin(p1):
            px1, py1 = p1
            return px1 ** 2 + py1 ** 2

        data = []
        for point in points:
            data.append((getDistanceFromOrigin(point), point[0], point[1]))

        return [[element[1], element[2]] for element in sorted(data, key=lambda x: x[0])[:k]]
