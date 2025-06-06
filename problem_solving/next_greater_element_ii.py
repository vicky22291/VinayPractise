"""
URL: https://leetcode.com/problems/next-greater-element-ii
"""
from typing import List


class Solution:
    def nextGreaterElements(self, nums: List[int]) -> List[int]:
        n = len(nums)
        ans, st = [-1] * n, []
        for i in range(2 * n - 1, -1, -1):
            while len(st) and nums[st[-1]] <= nums[i % n]:
                st.pop()
            if len(st):
                ans[i % n] = nums[st[-1]]
            st.append(i % n)
        return ans