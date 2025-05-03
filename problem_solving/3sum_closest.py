"""
URL: https://leetcode.com/problems/3sum-closest/

Given an integer array nums of length n and an integer target, find three integers in nums such that the sum is closest to target.

Return the sum of the three integers.

You may assume that each input would have exactly one solution.



Example 1:

Input: nums = [-1,2,1,-4], target = 1
Output: 2
Explanation: The sum that is closest to the target is 2. (-1 + 2 + 1 = 2).
Example 2:

Input: nums = [0,0,0], target = 1
Output: 0
Explanation: The sum that is closest to the target is 0. (0 + 0 + 0 = 0).


Constraints:

3 <= nums.length <= 500
-1000 <= nums[i] <= 1000
-104 <= target <= 104
"""
from bisect import bisect_right
from typing import List


class Solution:
    def threeSumClosest(self, nums: List[int], target: int) -> int:
        diff = 1_000_000_000
        nums.sort()
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                possible_third = target - nums[i] - nums[j]
                hi = bisect_right(nums, possible_third, j + 1)
                lo = hi - 1
                if hi < len(nums) and abs(possible_third - nums[hi]) < abs(diff):
                    diff = possible_third - nums[hi]
                if lo > j and abs(possible_third - nums[lo]) < abs(diff):
                    diff = possible_third - nums[lo]
            if diff == 0:
                break
        return target - diff