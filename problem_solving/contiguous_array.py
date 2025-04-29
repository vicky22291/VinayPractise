"""
URL: https://leetcode.com/problems/contiguous-array/

Given a binary array nums, return the maximum length of a contiguous subarray with an equal number of 0 and 1.



Example 1:

Input: nums = [0,1]
Output: 2
Explanation: [0, 1] is the longest contiguous subarray with an equal number of 0 and 1.
Example 2:

Input: nums = [0,1,0]
Output: 2
Explanation: [0, 1] (or [1, 0]) is a longest contiguous subarray with equal number of 0 and 1.
Example 3:

Input: nums = [0,1,1,1,1,1,0,0,0]
Output: 6
Explanation: [1,1,1,0,0,0] is the longest contiguous subarray with equal number of 0 and 1.


Constraints:

1 <= nums.length <= 105
nums[i] is either 0 or 1.
"""
from collections import defaultdict
from typing import List


class Solution:
    def findMaxLength(self, nums: List[int]) -> int:
        countMap = {0: -1}
        max_len = count = 0
        for i in range(len(nums)):
            count = count + (1 if nums[i] == 1 else -1)
            if count in countMap:
                max_len = max(max_len, i - countMap[count])
            else:
                countMap[count] = i
        return max_len