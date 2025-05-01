"""
URL: https://leetcode.com/problems/subarray-sum-equals-k/

Given an array of integers nums and an integer k, return the total number of subarrays whose sum equals to k.

A subarray is a contiguous non-empty sequence of elements within an array.



Example 1:

Input: nums = [1,1,1], k = 2
Output: 2
Example 2:

Input: nums = [1,2,3], k = 3
Output: 2


Constraints:

1 <= nums.length <= 2 * 104
-1000 <= nums[i] <= 1000
-107 <= k <= 107
"""
from typing import List


class Solution:
    def subarraySum(self, nums: List[int], k: int) -> int:
        n = len(nums)
        ans = 0
        for size in range(n):
            window_sum = sum(nums[:size+1])
            if window_sum == k:
                ans += 1
            for i in range(1, n - size):
                window_sum = window_sum - nums[i - 1] + nums[i + size]
                if window_sum == k:
                    ans += 1
        return ans

class Solution2:
    def subarraySum(self, nums: List[int], k: int) -> int:
        sum_s = count = 0
        data = {0: 1}
        for i in nums:
            sum_s += i
            if sum_s - k in data:
                count += data[sum_s - k]
            data[sum_s] = (data[sum_s] + 1) if sum_s in data else 1
        return count