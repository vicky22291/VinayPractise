"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/94/trees/631/
"""
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution(object):
    def sortedArrayToBST(self, nums):
        """
        :type nums: List[int]
        :rtype: TreeNode
        """
        l = len(nums)
        if l == 0:
            return None
        if l == 1:
            return TreeNode(val=nums[0], left=None, right=None)
        index = int(l / 2)
        left_node = right_node = None
        if index >= 1:
            left_node = self.sortedArrayToBST(nums[:index])
        if l >= 3:
            right_node = self.sortedArrayToBST(nums[index + 1:])
        return TreeNode(val=nums[index], left=left_node, right=right_node)