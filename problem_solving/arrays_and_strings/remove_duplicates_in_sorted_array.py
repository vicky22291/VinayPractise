"""
    https://leetcode.com/explore/featured/card/top-interview-questions-easy/92/array/727/
"""
class Solution(object):
    def removeDuplicates(self, nums):
        """
        :type nums: List[int]
        :rtype: int
        """
        index = 1
        while index < len(nums):
            if nums[index - 1] == nums[index]:
                nums.pop(index)
            else:
                index += 1