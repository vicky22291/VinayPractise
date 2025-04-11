"""
URL: https://leetcode.com/problems/meeting-rooms/description/


Given an array of meeting time intervals where intervals[i] = [starti, endi], determine if a person could attend all meetings.



Example 1:

Input: intervals = [[0,30],[5,10],[15,20]]
Output: false
Example 2:

Input: intervals = [[7,10],[2,4]]
Output: true


Constraints:

0 <= intervals.length <= 104
intervals[i].length == 2
0 <= starti < endi <= 106
"""
from typing import List


class Solution:
    def canAttendMeetings(self, intervals: List[List[int]]) -> bool:
        intervals = sorted(intervals, key=lambda x: x[0])
        last_complete = -1
        for interval in intervals:
            if last_complete > interval[0]:
                return False
            last_complete = interval[1]
        return True