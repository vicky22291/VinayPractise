"""
URL: https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/description
"""
from heapq import heapify, heappop
from typing import List


class HeapItem:
    def __init__(self, item, priority_function):
        self.item = item
        self.priority_function = priority_function

    def __lt__(self, other):
        # Use the priority function to compare
        return self.priority_function(self.item) < self.priority_function(other.item)

class Solution:
    def kthSmallest(self, matrix: List[List[int]], k: int) -> int:
        m = len(matrix)
        hparray = []
        for i in range(min(k, m)):
            hparray.append(HeapItem(matrix[i], lambda x: x[0]))
        heapify(hparray)
        poped_element = None
        for i in range(k):
            lowestRow = heappop(hparray)
            poped_element = lowestRow.item.pop(0)
            if len(lowestRow.item) > 0:
                heappush(hparray, lowestRow)
        return poped_element