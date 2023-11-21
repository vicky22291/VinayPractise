"""
    https://leetcode.com/explore/learn/card/dynamic-programming/632/common-patterns-in-dp-problems/4109/
"""
from functools import cache
from typing import List


class Solution:
    def minDifficulty(self, jobDifficulty: List[int], d: int) -> int:
        n = len(jobDifficulty)
        if n < d:
            return -1

        max_job_remaining = jobDifficulty[:]
        for i in range(n - 2, -1, -1):
            max_job_remaining[i] = max(max_job_remaining[i], max_job_remaining[i + 1])

        @cache
        def min_diff(i, days_remaining):
            if days_remaining == 1:
                return max_job_remaining[i]

            res = float('inf')
            daily_max_job_diff = 0

            for j in range(i, n - days_remaining + 1):
                daily_max_job_diff = max(daily_max_job_diff, jobDifficulty[j])
                res = min(res, daily_max_job_diff + min_diff(j + 1, days_remaining - 1))

            return res

        return min_diff(0, d)
