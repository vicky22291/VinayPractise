"""
URL: https://leetcode.com/problems/count-nodes-equal-to-average-of-subtree
"""
# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def averageOfSubtree(self, root: TreeNode) -> int:
        ans = 0
        def sub(node):
            nonlocal ans
            if node is None:
                return 0, 0
            n = s = 0
            nl, sl = sub(node.left)
            nr, sr = sub(node.right)
            if node.val == (sl + sr + node.val) // (nl + nr + 1):
                ans += 1
            return nl + nr + 1, sl + sr + node.val
        sub(root)
        return ans