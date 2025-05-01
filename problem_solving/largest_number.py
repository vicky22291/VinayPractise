"""
URL: https://leetcode.com/problems/largest-number/

Given a list of non-negative integers nums, arrange them such that they form the largest number and return it.

Since the result may be very large, so you need to return a string instead of an integer.



Example 1:

Input: nums = [10,2]
Output: "210"
Example 2:

Input: nums = [3,30,34,5,9]
Output: "9534330"


Constraints:

1 <= nums.length <= 100
0 <= nums[i] <= 109
"""
from typing import List


class Solution:
    def largestNumber(self, nums: List[int]) -> str:
        strings = [str(num) for num in nums]
        strings.sort(key=lambda num: num * 10, reverse=True)
        return "0" if strings[0] == "0" else "".join(strings)


sol = Solution()
print(sol.largestNumber([10,2]))
print(sol.largestNumber([3,30,34,5,9]))