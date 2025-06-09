"""
URL: https://leetcode.com/problems/maximum-profit-in-job-scheduling/
"""
from collections import defaultdict
from typing import List


class Solution:
    def jobScheduling(self, startTime: List[int], endTime: List[int], profit: List[int]) -> int:
        jobs = []
        for i in range(len(startTime)):
            jobs.append((startTime[i], 0, profit[i], endTime[i]))
            jobs.append((endTime[i], 1, profit[i], startTime[i]))
        jobs.sort()  # sorted by time, and then whether it's start or end

        dp = defaultdict(int)
        last_max = 0

        for i in range(len(startTime) * 2):
            t, isEnd, p, otherT = jobs[i]

            if isEnd == 0:  # start
                dp[t] = max(dp[t], last_max)
            else:
                dp[t] = max(dp[t], dp[otherT] + p, last_max)
                last_max = max(last_max, dp[t])

        return last_max