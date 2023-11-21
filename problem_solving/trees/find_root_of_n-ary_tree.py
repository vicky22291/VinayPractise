"""
    https://leetcode.com/problems/find-root-of-n-ary-tree/
"""
from typing import List


"""
# Definition for a Node.
class Node:
    def __init__(self, val=None, children=None):
        self.val = val
        self.children = children if children is not None else []
"""


class Solution:
    def findRoot(self, tree: List['Node']) -> 'Node':
        parentData = {}
        for node in tree:
            for child in node.children:
                parentData[child] = node
            if node not in parentData:
                parentData[node] = None
        for node, parent in parentData.items():
            if parent is None:
                return node