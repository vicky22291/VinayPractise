"""
    https://leetcode.com/problems/path-sum-iii/description/
"""
from typing import Optional


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def pathSum(self, root: Optional[TreeNode], targetSum: int) -> int:
        if root is None:
            return 0

        paths = 0

        def dfs(node, s, haveToTake):
            nonlocal paths

            if node.val == s:
                paths += 1
            if node.left:
                dfs(node.left, s - node.val, True)
                if not haveToTake:
                    dfs(node.left, s, False)
            if node.right:
                dfs(node.right, s - node.val, True)
                if not haveToTake:
                    dfs(node.right, s, False)

        dfs(root, targetSum, False)

        return paths