"""
URL: https://leetcode.com/problems/median-of-two-sorted-arrays/description
"""
from typing import List


class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        n1, n2 = len(nums1), len(nums2)
        n = n1 + n2

        def solve(k, l1, r1, l2, r2):
            if l1 > r1:
                return nums2[k - l1]
            if l2 > r2:
                return nums1[k - l2]

            m1, m2 = (l1 + r1) // 2, (l2 + r2) // 2
            mid1, mid2 = nums1[m1], nums2[m2]

            if m1 + m2 < k:
                if mid1 > mid2:
                    return solve(k, l1, r1, m2 + 1, r2)
                else:
                    return solve(k, m1 + 1, r1, l2, r2)
            else:
                if mid1 > mid2:
                    return solve(k, l1, m1 - 1, l2, r2)
                else:
                    return solve(k, l1, r1, l2, m2 - 1)

        if n % 2:
            return solve(n // 2, 0, n1 - 1, 0, n2 - 1)
        else:
            return (solve(n // 2 - 1, 0, n1 - 1, 0, n2 - 1) + solve(n // 2, 0, n1 - 1, 0, n2 - 1)) / 2