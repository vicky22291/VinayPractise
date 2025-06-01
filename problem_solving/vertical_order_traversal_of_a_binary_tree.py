"""
URL: https://leetcode.com/problems/vertical-order-traversal-of-a-binary-tree
"""
from typing import Optional, List


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def verticalTraversal(self, root: Optional[TreeNode]) -> List[List[int]]:
        node_list = []

        def DFS(node, row, column):
            if node is not None:
                node_list.append((column, row, node.val))
                # preorder DFS
                DFS(node.left, row + 1, column - 1)
                DFS(node.right, row + 1, column + 1)

        # step 1). construct the node list, with the coordinates
        DFS(root, 0, 0)

        # step 2). sort the node list globally, according to the coordinates
        node_list.sort()

        # step 3). retrieve the sorted results grouped by the column index
        ret = []
        curr_column_index = node_list[0][0]
        curr_column = []
        for column, row, value in node_list:
            if column == curr_column_index:
                curr_column.append(value)
            else:
                # end of a column, and start the next column
                ret.append(curr_column)
                curr_column_index = column
                curr_column = [value]
        # add the last column
        ret.append(curr_column)

        return ret