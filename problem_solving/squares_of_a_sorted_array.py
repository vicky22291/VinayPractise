"""
URL: https://leetcode.com/problems/squares-of-a-sorted-array/

Given an integer array nums sorted in non-decreasing order, return an array of the squares of each number sorted in non-decreasing order.



Example 1:

Input: nums = [-4,-1,0,3,10]
Output: [0,1,9,16,100]
Explanation: After squaring, the array becomes [16,1,0,9,100].
After sorting, it becomes [0,1,9,16,100].
Example 2:

Input: nums = [-7,-3,2,3,11]
Output: [4,9,9,49,121]


Constraints:

1 <= nums.length <= 104
-104 <= nums[i] <= 104
nums is sorted in non-decreasing order.


Follow up: Squaring each element and sorting the new array is very trivial, could you find an O(n) solution using a different approach?
"""
from typing import List


class Solution:
    def sortedSquares(self, nums: List[int]) -> List[int]:
        negative_descending = []
        positive_ascending = []
        for num in nums:
            if num < 0:
                negative_descending.insert(0, num)
            else:
                positive_ascending.append(num)
        result = []
        n_negative = len(negative_descending)
        n_positive = len(positive_ascending)
        pi = ni = 0
        while pi < n_positive and ni < n_negative:
            if abs(negative_descending[ni]) < positive_ascending[pi]:
                result.append(negative_descending[ni] ** 2)
                ni += 1
            else:
                result.append(positive_ascending[pi] ** 2)
                pi += 1
        while pi < n_positive:
            result.append(positive_ascending[pi] ** 2)
            pi += 1
        while ni < n_negative:
            result.append(negative_descending[ni] ** 2)
            ni += 1
        return result