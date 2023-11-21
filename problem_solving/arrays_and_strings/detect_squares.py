"""
    https://leetcode.com/problems/detect-squares/description/
"""
import collections
from typing import List


class DetectSquares:
    def __init__(self):
        self.points = collections.defaultdict(int)

    def add(self, point: List[int]) -> None:
        self.points[tuple(point)] += 1

    def count(self, point: List[int]) -> int:
        res = 0
        px, py = point
        for (x, y), count in self.points.items():
            if x != px and abs(px - x) == abs(py - y) and (px, y) in self.points and (x, py) in self.points:
                res += self.points[(px, y)] * self.points[(x, py)] * count
        return res