"""
URL: https://leetcode.com/problems/intersection-of-two-arrays
"""
from typing import List


class Solution:
    def intersection(self, nums1: List[int], nums2: List[int]) -> List[int]:
        s1, s2 = set(nums1), set(nums2)
        return list(s1.intersection(s2))