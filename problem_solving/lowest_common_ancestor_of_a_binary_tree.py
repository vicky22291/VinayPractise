"""
URL: https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/description/

Given a binary tree, find the lowest common ancestor (LCA) of two given nodes in the tree.

According to the definition of LCA on Wikipedia: “The lowest common ancestor is defined between two nodes p and q as the lowest node in T that has both p and q as descendants (where we allow a node to be a descendant of itself).”



Example 1:


Input: root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 1
Output: 3
Explanation: The LCA of nodes 5 and 1 is 3.
Example 2:


Input: root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 4
Output: 5
Explanation: The LCA of nodes 5 and 4 is 5, since a node can be a descendant of itself according to the LCA definition.
Example 3:

Input: root = [1,2], p = 1, q = 2
Output: 1


Constraints:

The number of nodes in the tree is in the range [2, 105].
-109 <= Node.val <= 109
All Node.val are unique.
p != q
p and q will exist in the tree.
"""
from typing import List


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, x):
        self.val = x
        self.left = None
        self.right = None

class Solution:
    def lowestCommonAncestor(self, root: TreeNode, p: TreeNode, q: TreeNode) -> TreeNode:
        def sub_lca(sr: TreeNode, p: TreeNode, q: TreeNode) -> List:
            if sr is None:
                return [None, False, False]
            lcal, lp_found, lq_found = sub_lca(sr.left, p, q)
            if lcal:
                return [lcal, lp_found, lq_found]
            lcar, rp_found, rq_found = sub_lca(sr.right, p, q)
            if lcar:
                return [lcar, rp_found, rq_found]
            if sr == p:
                if lq_found or rq_found:
                    return [sr, True, True]
                else:
                    return [None, True, False]
            if sr == q:
                if lp_found or rp_found:
                    return [sr, True, True]
                else:
                    return [None, False, True]
            if (lp_found or rp_found) and (lq_found or rq_found):
                return [sr, True, True]
            else:
                return [None, lp_found or rp_found, lq_found or rq_found]
        return sub_lca(root, p, q)[0]