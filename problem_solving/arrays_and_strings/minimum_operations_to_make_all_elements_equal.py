"""
    https://leetcode.com/problems/minimum-operations-to-make-all-array-elements-equal/description/
"""
import itertools
import bisect
from typing import List


class Solution:
    def minOperations(self, nums: List[int], queries: List[int]) -> List[int]:
        """
        ans = []
        for query in queries:
            count = 0
            for num in nums:
                count += abs(num - query)
            ans.append(count)
        return ans
        """
        nums.sort()
        ans, n, prefix = [], len(nums), [0] + list(itertools.accumulate(nums))
        for x in queries:
            i = bisect.bisect_left(nums, x)
            ans.append(x * (2 * i - n) + prefix[n] - 2 * prefix[i])
        return ans