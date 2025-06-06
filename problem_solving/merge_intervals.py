"""
URL: https://leetcode.com/problems/merge-intervals/

Given an array of intervals where intervals[i] = [starti, endi], merge all overlapping intervals, and return an array of the non-overlapping intervals that cover all the intervals in the input.



Example 1:

Input: intervals = [[1,3],[2,6],[8,10],[15,18]]
Output: [[1,6],[8,10],[15,18]]
Explanation: Since intervals [1,3] and [2,6] overlap, merge them into [1,6].
Example 2:

Input: intervals = [[1,4],[4,5]]
Output: [[1,5]]
Explanation: Intervals [1,4] and [4,5] are considered overlapping.


Constraints:

1 <= intervals.length <= 104
intervals[i].length == 2
0 <= starti <= endi <= 104
"""
from typing import List


class Solution:
    def merge(self, intervals: List[List[int]]) -> List[List[int]]:
        s_intervals = sorted(intervals, key=lambda x: x[0])
        result = []
        prev_interval = None
        for interval in s_intervals:
            if prev_interval is None:
                result.append(interval)
                prev_interval = interval
            elif prev_interval[1] < interval[0]:
                result.append(interval)
                prev_interval = interval
            else:
                result[-1] = [result[-1][0], max(prev_interval[1], interval[1])]
                prev_interval = result[-1]
        return result