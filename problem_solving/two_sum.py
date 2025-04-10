"""
URL: https://leetcode.com/problems/two-sum/description/

Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

You can return the answer in any order.



Example 1:

Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].
Example 2:

Input: nums = [3,2,4], target = 6
Output: [1,2]
Example 3:

Input: nums = [3,3], target = 6
Output: [0,1]


Constraints:

2 <= nums.length <= 104
-109 <= nums[i] <= 109
-109 <= target <= 109
Only one valid answer exists.


Follow-up: Can you come up with an algorithm that is less than O(n2) time complexity?
"""
from typing import List


class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        sorted_nums = sorted([[index, num] for index, num in enumerate(nums)], key=lambda x: x[1])
        start = 0
        end = len(nums) - 1
        while start < end:
            current_sum = sorted_nums[start][1] + sorted_nums[end][1]
            if current_sum == target:
                return [sorted_nums[start][0], sorted_nums[end][0]]
            elif current_sum > target:
                end -= 1
            else:
                start += 1
        return []