"""
URL: https://leetcode.com/problems/path-sum/
"""
from typing import Optional


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def hasPathSum(self, root: Optional[TreeNode], targetSum: int) -> bool:
        if root is None:
            return False

        def sub(sum_so_far, node):
            nonlocal targetSum
            if node.left is None and node.right is None:
                return sum_so_far + node.val == targetSum
            sl = sr = False
            if node.left:
                sl = sub(sum_so_far + node.val, node.left)
            if not sl and node.right:
                sr = sub(sum_so_far + node.val, node.right)
            return sl or sr

        return sub(0, root)