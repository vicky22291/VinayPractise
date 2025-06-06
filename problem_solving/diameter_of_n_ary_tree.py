"""
URL: https://leetcode.com/problems/diameter-of-n-ary-tree
"""
from heapq import heapify, heappop
from typing import Optional, List


# Definition for a Node.
class Node:
    def __init__(self, val: Optional[int] = None, children: Optional[List['Node']] = None):
        self.val = val
        self.children = children if children is not None else []

class Solution:
    def diameter(self, root: 'Node') -> int:
        """
        :type root: 'Node'
        :rtype: int
        """
        def sub(node):
            heights = []
            max_d = -1
            for child in node.children:
                d, h = sub(child)
                heights.append(-h)
                max_d = max(d, max_d)
            if len(heights) == 1:
                return max(-heights[0] + 1, max_d), -heights[0] + 1
            elif len(heights) == 0:
                return 1, 1
            else:
                heapify(heights)
                h1 = -heappop(heights)
                h2 = -heappop(heights)
                return max(h1 + h2 + 1, max_d), h1 + 1
        return sub(root)[0] - 1