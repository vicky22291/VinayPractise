"""
URL: https://leetcode.com/problems/meeting-rooms-ii/

Given an array of meeting time intervals intervals where intervals[i] = [starti, endi], return the minimum number of conference rooms required.



Example 1:

Input: intervals = [[0,30],[5,10],[15,20]]
Output: 2
Example 2:

Input: intervals = [[7,10],[2,4]]
Output: 1


Constraints:

1 <= intervals.length <= 104
0 <= starti < endi <= 106
"""
from typing import List


class Solution:
    def minMeetingRooms(self, intervals: List[List[int]]) -> int:
        n = len(intervals)
        if n == 0:
            return 0
        sorted_starts = sorted(intervals, key=lambda x: x[0])
        sorted_ends = sorted(intervals, key=lambda x: x[1])
        sp = ep = used_rooms = 0
        while sp < n:
            if sorted_starts[sp] >= sorted_ends[ep]:
                used_rooms -= 1
                ep += 1
            used_rooms += 1
            sp += 1
        return used_rooms