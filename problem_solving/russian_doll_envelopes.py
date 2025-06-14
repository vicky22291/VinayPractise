"""
URL: https://leetcode.com/problems/russian-doll-envelopes/description
"""
from bisect import bisect_left
from typing import List


class Solution:
    def maxEnvelopes(self, envelopes: List[List[int]]) -> int:
        envelopes.sort(key=lambda x: x[0])

        def lis(arr):
            increasingSequences = []
            for num in arr:
                i = bisect_left(increasingSequences, num)
                if i == len(increasingSequences):
                    increasingSequences.append(num)
                else:
                    increasingSequences[i] = num
            return len(increasingSequences)
        return lis([ele[1] for ele in envelopes])