"""
URL: https://leetcode.com/problems/move-zeroes/description/

Given an integer array nums, move all 0's to the end of it while maintaining the relative order of the non-zero elements.

Note that you must do this in-place without making a copy of the array.



Example 1:

Input: nums = [0,1,0,3,12]
Output: [1,3,12,0,0]
Example 2:

Input: nums = [0]
Output: [0]


Constraints:

1 <= nums.length <= 104
-231 <= nums[i] <= 231 - 1


Follow up: Could you minimize the total number of operations done?
"""
from typing import List


class Solution:
    def moveZeroes(self, nums: List[int]) -> None:
        """
        Do not return anything, modify nums in-place instead.
        """
        if len(nums) == 1:
            return
        indexes = []
        ## First pass
        for index, num in enumerate(nums):
            if num == 0:
                indexes.append(index)

        ## Second pass
        num_of_zeroes = len(indexes)
        if num_of_zeroes == 0:
            return
        num_of_elements = len(nums)

        ri = indexes[0]
        wi = indexes[0]
        while ri < num_of_elements:
            if nums[ri] != 0:
                nums[wi] = nums[ri]
                wi += 1
            ri += 1

        ## Third Pass
        for i in range(num_of_zeroes):
            nums[-(i + 1)] = 0



