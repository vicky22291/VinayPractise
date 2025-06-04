"""
URL: https://leetcode.com/problems/exclusive-time-of-functions
"""
from typing import List


class Solution:
    def exclusiveTime(self, n: int, logs: List[str]) -> List[int]:
        times = [0] * n
        stack = []
        last_time = 0
        for log in logs:
            fid, action, tm = log.split(":")
            if action == 'start':
                if len(stack):
                    times[int(stack[-1])] += int(tm) - int(last_time) - 1
                stack.append(fid)
            else:
                if len(stack):
                    times[int(stack.pop())] += int(tm) - int(last_time) + 1
            last_time = tm
        return times