"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/94/trees/625/
"""
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def isValidBST(self, root: Optional[TreeNode]) -> bool:
        def traverse(node, soFar):
            if node.left:
                soFar, valid = traverse(node.left, soFar)
                if not valid:
                    return soFar, False
            if soFar is not None and soFar >= node.val:
                return soFar, False
            soFar = node.val
            if node.right:
                soFar, valid = traverse(node.right, soFar)
                if not valid:
                    return soFar, False
            return soFar, True

        return traverse(root, None)[1]