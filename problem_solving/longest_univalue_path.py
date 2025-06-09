"""
URL: https://leetcode.com/problems/longest-univalue-path/description/
"""
from typing import Optional


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def longestUnivaluePath(self, root: Optional[TreeNode]) -> int:
        def sub(node):
            if node is None or (node.left is None and node.right is None):
                return 0, 0
            el, ml = sub(node.left)
            er, mr = sub(node.right)
            e = ans = 0
            if node.left and node.val == node.left.val:
                e += el + 1
                ans = el + 1
            if node.right and node.val == node.right.val:
                e += er + 1
                ans = max(ans, er + 1)
            return ans, max(e, ml, mr)
        return sub(root)[1]
