"""
URL: https://leetcode.com/problems/binary-tree-zigzag-level-order-traversal/description/

Given the root of a binary tree, return the zigzag level order traversal of its nodes' values. (i.e., from left to right, then right to left for the next level and alternate between).



Example 1:


Input: root = [3,9,20,null,null,15,7]
Output: [[3],[20,9],[15,7]]
Example 2:

Input: root = [1]
Output: [[1]]
Example 3:

Input: root = []
Output: []


Constraints:

The number of nodes in the tree is in the range [0, 2000].
-100 <= Node.val <= 100
"""
from collections import deque
from typing import Optional, List


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def zigzagLevelOrder(self, root: Optional[TreeNode]) -> List[List[int]]:
        if root is None:
            return []
        nextQueue = deque()
        queue = deque([root])
        result = [[]]
        while len(queue):
            cur = queue.popleft()
            result[-1].append(cur.val)
            if cur.left:
                nextQueue.append(cur.left)
            if cur.right:
                nextQueue.append(cur.right)
            if len(queue) == 0:
                queue, nextQueue = nextQueue, queue
                if len(result) % 2 == 0:
                    result[-1].reverse()
                if len(queue):
                    result.append([])
        return result