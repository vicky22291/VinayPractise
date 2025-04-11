"""
URL: https://leetcode.com/problems/balanced-binary-tree/

Given a binary tree, determine if it is height-balanced.



Example 1:


Input: root = [3,9,20,null,null,15,7]
Output: true
Example 2:


Input: root = [1,2,2,3,3,null,null,4,4]
Output: false
Example 3:

Input: root = []
Output: true


Constraints:

The number of nodes in the tree is in the range [0, 5000].
-104 <= Node.val <= 104
"""

# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
from typing import Optional


class Solution:
    def isBalanced(self, root: Optional[TreeNode]) -> bool:
        def sub_isBalanced(root: Optional[TreeNode]) -> [bool, int]:
            if root is None:
                return [True, 0]
            left_isBalanced, left_height = sub_isBalanced(root.left)
            right_isBalanced, right_height = sub_isBalanced(root.right)
            if not(left_isBalanced and right_isBalanced) or abs(left_height - right_height) > 1:
                return [False, -1]
            return [True, max(left_height, right_height) + 1]
        return sub_isBalanced(root)[0]

sol = Solution()
print(sol.isBalanced(TreeNode(3, TreeNode(9), TreeNode(20, TreeNode(15), TreeNode(7)))))
print(sol.isBalanced(TreeNode(1, TreeNode(2))))