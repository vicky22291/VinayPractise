"""
URL: https://leetcode.com/problems/path-sum-iii/

Given the root of a binary tree and an integer targetSum, return the number of paths where the sum of the values along the path equals targetSum.

The path does not need to start or end at the root or a leaf, but it must go downwards (i.e., traveling only from parent nodes to child nodes).



Example 1:


Input: root = [10,5,-3,3,2,null,11,3,-2,null,1], targetSum = 8
Output: 3
Explanation: The paths that sum to 8 are shown.
Example 2:

Input: root = [5,4,8,11,null,13,4,7,2,null,null,5,1], targetSum = 22
Output: 3


Constraints:

The number of nodes in the tree is in the range [0, 1000].
-109 <= Node.val <= 109
-1000 <= targetSum <= 1000
"""
from collections import defaultdict
from typing import Optional


# Definition for a binary tree node.
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
class Solution:
    def pathSum(self, root: Optional[TreeNode], targetSum: int) -> int:
        nPaths = 0

        def sub(node, s, taken):
            nonlocal nPaths
            if node is None:
                return
            if s == node.val:
                nPaths += 1
            if node.left:
                sub(node.left, s - node.val, True)
                if not taken:
                    sub(node.left, s, False)
            if node.right:
                sub(node.right, s - node.val, True)
                if not taken:
                    sub(node.right, s, False)

        sub(root, targetSum, False)
        return nPaths

class Solution2:
    def pathSum(self, root: Optional[TreeNode], targetSum: int) -> int:
        nPaths, sums = 0, defaultdict(int)

        def dfs(node, cur_sum):
            nonlocal nPaths, sums, targetSum
            if node is None:
                return
            cur_sum += node.val
            if cur_sum == targetSum:
                nPaths += 1
            nPaths += sums[cur_sum - targetSum]
            sums[cur_sum] += 1
            dfs(node.left, cur_sum)
            dfs(node.right, cur_sum)
            sums[cur_sum] += 1

        dfs(root, 0)
        return nPaths


