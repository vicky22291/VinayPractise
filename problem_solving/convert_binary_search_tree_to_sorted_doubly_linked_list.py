"""
URL: https://leetcode.com/problems/convert-binary-search-tree-to-sorted-doubly-linked-list
"""

# Definition for a Node.
class Node:
    def __init__(self, val, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def treeToDoublyList(self, root: 'Optional[Node]') -> 'Optional[Node]':
        head = None

        def traverse(node):
            nonlocal head
            if node is None:
                return None, None
            elif node.left is None and node.right is None:
                return node, node
            ll, lr = traverse(node.left)
            rl, rr = traverse(node.right)

            if lr:
                lr.right, node.left = node, lr
            if rl:
                node.right, rl.left = rl, node
            return ll if ll else node, rr if rr else node
        head, r = traverse(root)
        if r:
            r.right, head.left = head, r
        return head