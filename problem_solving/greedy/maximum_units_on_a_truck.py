from typing import List


"""
    https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/709/greedy/4676/
"""


class Solution:
    def maximumUnits(self, boxTypes: List[List[int]], truckSize: int) -> int:
        boxTypes = sorted(boxTypes, key=lambda x: x[1], reverse=True)
        ans = 0
        index = 0
        while truckSize and index < len(boxTypes):
            num, count = boxTypes[index]
            ans += min(num, truckSize) * count
            truckSize -= min(num, truckSize)
            if truckSize:
                index += 1
        return ans