from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def isSubtree(self, root: Optional[TreeNode], subRoot: Optional[TreeNode]) -> bool:
        def traverse(n, sn, found):
            if found:
                if (not n.val != sn.val) or \
                        (not n.left and sn.left) or (n.left and not sn.left) or \
                        (not n.right and sn.right) or (n.right and not sn.right):
                    return False
                if n.left and not traverse(n.left, sn.left, found):
                    return False
                if n.right and not traverse(n.right, sn.right, found):
                    return False
                return True
            else:
                if n.val == sn.val:
                    found = True
                isSubTree = False
                if n.left:
                    isSubTree = traverse(n.left, sn.left if found else sn, found)
                if isSubTree:
                    return True
                if n.right:
                    isSubTree = traverse(n.right, sn.right if found else sn, found)
                return isSubTree

        return traverse(root, subRoot, False)
