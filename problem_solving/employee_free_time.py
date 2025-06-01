"""
URL: https://leetcode.com/problems/employee-free-time/description/
"""
# Definition for an Interval.
class Interval:
    def __init__(self, start: int = None, end: int = None):
        self.start = start
        self.end = end

class Solution:
    def employeeFreeTime(self, schedule: '[[Interval]]') -> '[Interval]':
        flattened = [i for employee in schedule for i in employee]
        intervals = sorted(flattened, key=lambda x: x.start)

        merged = []
        for interval in intervals:
            if not merged or merged[-1].end < interval.start:
                merged.append(interval)
            else:
                merged[-1].end = max(merged[-1].end, interval.end)

        free_times = []
        for i in range(1, len(merged)):
            start = merged[i - 1].end
            end = merged[i].start
            free_times.append(Interval(start, end))

        return free_times