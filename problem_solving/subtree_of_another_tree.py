"""
URL: https://leetcode.com/problems/subtree-of-another-tree/description/

A subtree of a binary tree tree is a tree that consists of a node in tree and all of this node's descendants. The tree tree could also be considered as a subtree of itself.



Example 1:


Input: root = [3,4,5,1,2], subRoot = [4,1,2]
Output: true
Example 2:


Input: root = [3,4,5,1,2,null,null,null,null,0], subRoot = [4,1,2]
Output: false


Constraints:

The number of nodes in the root tree is in the range [1, 2000].
The number of nodes in the subRoot tree is in the range [1, 1000].
-104 <= root.val <= 104
-104 <= subRoot.val <= 104
"""
from typing import Optional


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def isSubtree(self, root: Optional[TreeNode], subRoot: Optional[TreeNode]) -> bool:
        def sub(actual: TreeNode, reference: TreeNode, found: bool) -> bool:
            if found:
                if actual is None and reference is not None:
                    return False
                elif actual is not None and reference is None:
                    return False
                elif actual is None and reference is None:
                    return True
                elif actual.val != reference.val:
                    return False
                else:
                    is_found_in_left = sub(actual.left, reference.left, found)
                    is_found_in_right = sub(actual.right, reference.right, found)
                    return is_found_in_left and is_found_in_right
            if actual is None and reference is not None:
                return False
            elif actual is not None and reference is None:
                return False
            elif actual is None and reference is None:
                return True
            if actual.val == reference.val:
                is_found_in_left = sub(actual.left, reference.left, True)
                is_found_in_right = sub(actual.right, reference.right, True)
                if is_found_in_left and is_found_in_right:
                    return True
                else:
                    is_found_in_left = sub(actual.left, reference, False)
                    is_found_in_right = sub(actual.right, reference, False)
                    return is_found_in_left or is_found_in_right
            else:
                is_found_in_left = sub(actual.left, reference, False)
                is_found_in_right = sub(actual.right, reference, False)
                return is_found_in_left or is_found_in_right
        return sub(root, subRoot, False)