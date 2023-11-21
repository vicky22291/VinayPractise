"""
    https://leetcode.com/problems/two-sum-bsts/
"""
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def twoSumBSTs(self, root1: Optional[TreeNode], root2: Optional[TreeNode], target: int) -> bool:
        def search(node, value):
            if node.val == value:
                return True
            elif node.val > value:
                return node.left and search(node.left, value)
            else:
                return node.right and search(node.right, value)

        def traverse(node, target):
            nonlocal root2

            if search(root2, target - node.val):
                return True
            if node.left and traverse(node.left, target):
                return True
            if node.right and traverse(node.right, target):
                return True
            return False

        return traverse(root1, target)