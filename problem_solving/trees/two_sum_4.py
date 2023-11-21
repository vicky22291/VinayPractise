"""
    https://leetcode.com/problems/two-sum-iv-input-is-a-bst/
"""
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def findTarget(self, root: Optional[TreeNode], k: int) -> bool:
        nums = []

        def traverse(node):
            if node.left:
                traverse(node.left)
            nums.append(node.val)
            if node.right:
                traverse(node.right)

        traverse(root)

        left = 0
        right = len(nums) - 1
        while left < right:
            sumOfLeftRight = nums[left] + nums[right]
            if sumOfLeftRight > k:
                right -= 1
            elif sumOfLeftRight < k:
                left += 1
            else:
                return True
        return False