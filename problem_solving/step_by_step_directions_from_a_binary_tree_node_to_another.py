"""
URL: https://leetcode.com/problems/step-by-step-directions-from-a-binary-tree-node-to-another
"""
# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
from typing import Optional


class Solution:
    def getDirections(self, root: Optional[TreeNode], startValue: int, destValue: int) -> str:
        if root is None:
            return ""
        parents = {}

        def traverseAndFind(node, parent):
            nonlocal parents
            parents[node] = parent
            return_val = None
            if node.left:
                val = traverseAndFind(node.left, node)
                if val:
                    return_val = val
            if node.right:
                val = traverseAndFind(node.right, node)
                if val:
                    return_val = val
            if node.val == startValue:
                return node
            else:
                return return_val

        start = traverseAndFind(root, None)

        q, nq, seen = [(start, "")], [], set()
        count = 0
        while len(q):
            cur, string = q.pop()
            seen.add(cur.val)
            if parents[cur]:
                if parents[cur].val == destValue:
                    return string + "U"
                elif parents[cur].val not in seen:
                    nq.append((parents[cur], string + "U"))
            if cur.left:
                if cur.left.val == destValue:
                    return string + "L"
                elif cur.left.val not in seen:
                    nq.append((cur.left, string + "L"))
            if cur.right:
                if cur.right.val == destValue:
                    return string + "R"
                elif cur.right.val not in seen:
                    nq.append((cur.right, string + "R"))
            if len(q) == 0:
                q, nq = nq, q
                count += 1
        return ""