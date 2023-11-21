"""
    https://leetcode.com/problems/partition-to-k-equal-sum-subsets/
"""
import collections
import unittest
from typing import List


class Solution:
    def canPartitionKSubsets(self, nums: List[int], k: int) -> bool:
        """"""
        if sum(nums) % k:
            return False
        sumPerSet = sum(nums) // k
        arr = collections.deque(nums)

        def dfs(available, curSet):
            nonlocal sumPerSet

            if not available:
                return sum(curSet) == sumPerSet
            if curSet and sum(curSet) == sumPerSet:
                curSet = []
            for i in range(len(available)):
                num = available.popleft()
                if num <= sumPerSet - (sum(curSet) if curSet else 0):
                    curSet.append(num)
                    if dfs(available, curSet):
                        return True
                    curSet.pop()
                available.append(num)
            return False

        return dfs(arr, [])



class SolutionTest(unittest.TestCase):
    def testSample(self):
        sol = Solution()
        self.assertTrue(sol.canPartitionKSubsets([4, 3, 2, 3, 5, 2, 1], 4))

    def testSample2(self):
        sol = Solution()
        self.assertTrue(sol.canPartitionKSubsets([815, 625, 3889, 4471, 60, 494, 944, 1118, 4623, 497, 771, 679, 1240, 202, 601, 883], 3))
