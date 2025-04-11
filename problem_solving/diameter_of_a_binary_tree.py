"""
URL: https://leetcode.com/problems/diameter-of-binary-tree/description/

Given the root of a binary tree, return the length of the diameter of the tree.

The diameter of a binary tree is the length of the longest path between any two nodes in a tree. This path may or may not pass through the root.

The length of a path between two nodes is represented by the number of edges between them.



Example 1:


Input: root = [1,2,3,4,5]
Output: 3
Explanation: 3 is the length of the path [4,2,1,3] or [5,2,1,3].
Example 2:

Input: root = [1,2]
Output: 1


Constraints:

The number of nodes in the tree is in the range [1, 104].
-100 <= Node.val <= 100
"""
from typing import Optional


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def diameterOfBinaryTree(self, root: Optional[TreeNode]) -> int:
        if root is None:
            return 0
        def heightAndDiameter(r: Optional[TreeNode]) -> (int, int):
            if r.left is None and r.right is None:
                return 1, 0
            hls = hrs = dl = dr = 0
            if r.left:
                hls, dl = heightAndDiameter(r.left)
            if r.right:
                hrs, dr = heightAndDiameter(r.right)
            h = max(hls, hrs) + 1
            return h, max(h - 1, dl, dr)
        return heightAndDiameter(root)[1]