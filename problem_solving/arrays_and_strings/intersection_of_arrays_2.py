"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/92/array/674/
"""
from typing import List
from collections import Counter


class Solution:
    def intersect(self, nums1: List[int], nums2: List[int]) -> List[int]:
        count1 = Counter(nums1)
        count2 = Counter(nums2)
        ans = []
        for key, value in count1.items():
            if key in count2:
                for i in range(min(value, count2[key])):
                    ans.append(key)
        return ans
