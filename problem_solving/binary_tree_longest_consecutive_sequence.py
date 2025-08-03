"""
URL: https://leetcode.com/problems/binary-tree-longest-consecutive-sequence/
"""
from typing import Optional


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def longestConsecutive(self, root: Optional[TreeNode]) -> int:
        if root is None:
            return 0
        def dfs(node: TreeNode, parent_node: Optional[TreeNode], seq_length_so_far):
            if parent_node is None or node.val - parent_node.val != 1:
                seq_length = 1
            else:
                seq_length = seq_length_so_far + 1
            max_seq_length_from_child = 0
            if node.left:
                max_seq_length_from_child = max(max_seq_length_from_child, dfs(node.left, node, seq_length))
            if node.right:
                max_seq_length_from_child = max(max_seq_length_from_child, dfs(node.right, node, seq_length))
            return max(seq_length, seq_length_so_far, max_seq_length_from_child)
        return dfs(root, None, 0)