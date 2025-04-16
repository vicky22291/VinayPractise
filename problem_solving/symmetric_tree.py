"""
URL: https://leetcode.com/problems/symmetric-tree/description/

Given the root of a binary tree, check whether it is a mirror of itself (i.e., symmetric around its center).



Example 1:


Input: root = [1,2,2,3,4,4,3]
Output: true
Example 2:


Input: root = [1,2,2,null,3,null,3]
Output: false


Constraints:

The number of nodes in the tree is in the range [1, 1000].
-100 <= Node.val <= 100


Follow up: Could you solve it both recursively and iteratively?
"""
from typing import Optional


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def isSymmetric(self, root: Optional[TreeNode]) -> bool:
        visited = dict()
        def sub_isSymmetric(node: TreeNode, mirror_node: TreeNode) -> bool:
            if node is None and mirror_node is not None:
                return False
            elif node is not None and mirror_node is None:
                return False
            elif node is None and mirror_node is None:
                return True
            elif node.val != mirror_node.val:
                return False
            if node in visited:
                return visited[node]
            left_symmetry = sub_isSymmetric(node.left, mirror_node.right)
            right_symmetry = sub_isSymmetric(node.right, mirror_node.left)
            visited[node] = left_symmetry and right_symmetry
            return left_symmetry and right_symmetry
        return sub_isSymmetric(root, root)
