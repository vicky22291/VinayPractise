"""
URL: https://leetcode.com/problems/longest-consecutive-sequence/description/

Given an unsorted array of integers nums, return the length of the longest consecutive elements sequence.

You must write an algorithm that runs in O(n) time.



Example 1:

Input: nums = [100,4,200,1,3,2]
Output: 4
Explanation: The longest consecutive elements sequence is [1, 2, 3, 4]. Therefore its length is 4.
Example 2:

Input: nums = [0,3,7,2,5,8,4,6,0,1]
Output: 9
Example 3:

Input: nums = [1,0,1,2]
Output: 3


Constraints:

0 <= nums.length <= 105
-109 <= nums[i] <= 109

"""
from collections import defaultdict
from typing import List


class Solution:
    def longestConsecutive(self, nums: List[int]) -> int:
        numbers_higher = {}
        max_consecutive = 0
        for num in nums:
            numbers_higher[num] = (numbers_higher[num - 1] + 1) if num - 1 in numbers_higher else 1
            max_consecutive = max(max_consecutive, numbers_higher[num])
            if num + 1 in numbers_higher:
                cur = num
                while cur + 1 in numbers_higher:
                    numbers_higher[cur + 1] = numbers_higher[cur] + 1
                    max_consecutive = max(max_consecutive, numbers_higher[cur + 1])
                    cur += 1
        return max_consecutive

class Solution1:
    def longestConsecutive(self, nums: List[int]) -> int:
        longest_streak = 0
        num_set = set(nums)

        for num in num_set:
            if num - 1 not in num_set:
                current_num = num
                current_streak = 1

                while current_num + 1 in num_set:
                    current_num += 1
                    current_streak += 1

                longest_streak = max(longest_streak, current_streak)

        return longest_streak