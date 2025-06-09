"""
URL: https://leetcode.com/problems/binary-tree-tilt/
"""
from typing import Optional


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def findTilt(self, root: Optional[TreeNode]) -> int:
        if root is None:
            return 0
        def sub(node):
            sl = sr = tl = tr = 0
            if node.left:
                sl, tl = sub(node.left)
            if node.right:
                sr, tr = sub(node.right)
            return sl + sr + node.val, tl + tr + abs(sl - sr)
        return sub(root)[1]