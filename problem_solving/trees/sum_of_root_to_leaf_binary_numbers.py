from typing import Optional


"""
    https://leetcode.com/problems/sum-of-root-to-leaf-binary-numbers/
"""


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def sumRootToLeaf(self, root: Optional[TreeNode]) -> int:
        def traverse(node, curNum, curSum):
            num = curNum * 2 + node.val
            if node.left is None and node.right is None:
                return curSum + num
            if node.left:
                curSum = traverse(node.left, num, curSum)
            if node.right:
                curSum = traverse(node.right, num, curSum)
            return curSum

        return traverse(root, 0, 0)