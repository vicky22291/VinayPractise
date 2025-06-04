"""
URL: https://leetcode.com/problems/dot-product-of-two-sparse-vectors
"""
from typing import List


class SparseVector:
    def __init__(self, nums: List[int]):
        self.short = []
        self.n = len(nums)
        for i, n in enumerate(nums):
            if n > 0:
                self.short.append([i, n])

    # Return the dotProduct of two sparse vectors
    def dotProduct(self, vec: 'SparseVector') -> int:
        l = r = 0
        nl = len(self.short)
        nr = len(vec.short)
        dot = 0
        while l < nl and r < nr:
            while l < nl and r < nr and self.short[l][0] < vec.short[r][0]:
                l += 1
            while r < nr and l < nl and vec.short[r][0] < self.short[l][0]:
                r += 1
            if l < nl and r < nr and self.short[l][0] == vec.short[r][0]:
                dot += self.short[l][1] * vec.short[r][1]
                l += 1
                r += 1
        return dot

# Your SparseVector object will be instantiated and called as such:
# v1 = SparseVector(nums1)
# v2 = SparseVector(nums2)
# ans = v1.dotProduct(v2)