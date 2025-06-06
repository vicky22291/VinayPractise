"""
URL: https://leetcode.com/problems/clone-binary-tree-with-random-pointer
"""
from typing import Optional


# Definition for Node.
class Node:
    def __init__(self, val=0, left=None, right=None, random=None):
        self.val = val
        self.left = left
        self.right = right
        self.random = random

class NodeCopy:
    def __init__(self, val=0, left=None, right=None, random=None):
        self.val = val
        self.left = left
        self.right = right
        self.random = random

class Solution:
    def copyRandomBinaryTree(self, root: Optional[Node]) -> Optional[NodeCopy]:
        if root is None:
            return None
        nodes = {}
        def first(node):
            nodes[node] = NodeCopy(node.val)
            if node.left:
                first(node.left)
                nodes[node].left = nodes[node.left]
            if node.right:
                first(node.right)
                nodes[node].right = nodes[node.right]
        first(root)
        for node, nodeCopy in nodes.items():
            if node.random:
                nodeCopy.random = nodes[node.random]
        return nodes[root]