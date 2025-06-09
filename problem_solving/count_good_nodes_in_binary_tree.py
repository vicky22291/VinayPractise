"""
URL: https://leetcode.com/problems/count-good-nodes-in-binary-tree/description/
"""

# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def goodNodes(self, root: TreeNode) -> int:
        ans = 0
        def sub(node, max_so_far):
            nonlocal ans
            if node.val >= max_so_far:
                ans += 1
            if node.left:
                sub(node.left, max(max_so_far, node.val))
            if node.right:
                sub(node.right, max(max_so_far, node.val))
        sub(root, -1000000000)
        return ans