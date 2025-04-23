"""
URL: https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/description/

Given two integer arrays preorder and inorder where preorder is the preorder traversal of a binary tree and inorder is the inorder traversal of the same tree, construct and return the binary tree.



Example 1:


Input: preorder = [3,9,20,15,7], inorder = [9,3,15,20,7]
Output: [3,9,20,null,null,15,7]
Example 2:

Input: preorder = [-1], inorder = [-1]
Output: [-1]


Constraints:

1 <= preorder.length <= 3000
inorder.length == preorder.length
-3000 <= preorder[i], inorder[i] <= 3000
preorder and inorder consist of unique values.
Each value of inorder also appears in preorder.
preorder is guaranteed to be the preorder traversal of the tree.
inorder is guaranteed to be the inorder traversal of the tree.
"""
from typing import List, Optional


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def buildTree(self, preorder: List[int], inorder: List[int]) -> Optional[TreeNode]:
        inorder_indexes = {number: index for index, number in enumerate(inorder)}
        p_start = 0
        def construct(i_start, i_end):
            nonlocal p_start
            if i_start > i_end:
                return None
            elif i_start == i_end:
                root_index = inorder_indexes[preorder[p_start]]
                p_start += 1
                return TreeNode(val=inorder[root_index])
            else:
                root_index = inorder_indexes[preorder[p_start]]
                p_start += 1
                return TreeNode(
                    val=inorder[root_index],
                    left=construct(i_start, root_index - 1),
                    right=construct(root_index + 1, i_end)
                )
        return construct(0, len(inorder) - 1)

sol = Solution()
print(sol.buildTree([3,9,20,15,7], [9,3,15,20,7]))