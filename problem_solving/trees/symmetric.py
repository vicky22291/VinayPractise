"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/94/trees/627/
"""
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def isValidBST(self, root: Optional[TreeNode]) -> bool:
        def traverse(left, right):
            if left is None and right is None:
                return True
            elif (left is None and right is not None) or \
                    (left is not None and right is None) or \
                    left.val != right.val:
                return False
            return traverse(left.left, right.right) and traverse(left.right, right.left)
        return traverse(root.left, root.right)