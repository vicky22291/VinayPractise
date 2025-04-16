"""
URL: https://leetcode.com/problems/binary-tree-level-order-traversal/description/

Given the root of a binary tree, return the level order traversal of its nodes' values. (i.e., from left to right, level by level).



Example 1:


Input: root = [3,9,20,null,null,15,7]
Output: [[3],[9,20],[15,7]]
Example 2:

Input: root = [1]
Output: [[1]]
Example 3:

Input: root = []
Output: []


Constraints:

The number of nodes in the tree is in the range [0, 2000].
-1000 <= Node.val <= 1000
"""
from typing import Optional, List


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def levelOrder(self, root: Optional[TreeNode]) -> List[List[int]]:
        if root is None:
            return []
        result = [[root.val]]
        queue = [root]
        next_queue = []
        while len(queue):
            node = queue.pop(0)
            if node.left:
                next_queue.append(node.left)
            if node.right:
                next_queue.append(node.right)
            if len(queue) == 0 and len(next_queue):
                queue, next_queue = next_queue, queue
                result.append([node.val for node in queue])
        return result