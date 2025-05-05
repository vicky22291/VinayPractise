"""
URL:https://leetcode.com/problems/binary-tree-vertical-order-traversal/

Given the root of a binary tree, return the vertical order traversal of its nodes' values. (i.e., from top to bottom, column by column).

If two nodes are in the same row and column, the order should be from left to right.



Example 1:


Input: root = [3,9,20,null,null,15,7]
Output: [[9],[3,15],[20],[7]]
Example 2:


Input: root = [3,9,8,4,0,1,7]
Output: [[4],[9],[3,0,1],[8],[7]]
Example 3:


Input: root = [1,2,3,4,10,9,11,null,5,null,null,null,null,null,null,null,6]
Output: [[4],[2,5],[1,10,9,6],[3],[11]]


Constraints:

The number of nodes in the tree is in the range [0, 100].
-100 <= Node.val <= 100
"""
from collections import defaultdict, deque
from typing import Optional, List


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def verticalOrder(self, root: Optional[TreeNode]) -> List[List[int]]:
        if root is None:
            return []
        cols = defaultdict(list)
        queue, next_queue = deque(), deque()
        queue.append(((root, 0)))
        while len(queue):
            node, col = queue.popleft()
            cols[col].append(node.val)
            if node.left:
                next_queue.append((node.left, col - 1))
            if node.right:
                next_queue.append((node.right, col + 1))
            if len(queue) == 0:
                queue, next_queue = next_queue, queue
        cols = sorted([(key, vals) for key, vals in cols.items()], key=lambda x: x[0])
        return [vals for _, vals in cols]
