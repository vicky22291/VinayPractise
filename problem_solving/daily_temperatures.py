"""
URL: https://leetcode.com/problems/daily-temperatures/

Given an array of integers temperatures represents the daily temperatures, return an array answer such that answer[i] is the number of days you have to wait after the ith day to get a warmer temperature. If there is no future day for which this is possible, keep answer[i] == 0 instead.



Example 1:

Input: temperatures = [73,74,75,71,69,72,76,73]
Output: [1,1,4,2,1,1,0,0]
Example 2:

Input: temperatures = [30,40,50,60]
Output: [1,1,1,0]
Example 3:

Input: temperatures = [30,60,90]
Output: [1,1,0]


Constraints:

1 <= temperatures.length <= 105
30 <= temperatures[i] <= 100
"""
from typing import List


class Solution:
    def dailyTemperatures(self, temperatures: List[int]) -> List[int]:
        n = len(temperatures)
        arr = sorted([(val, index) for index, val in enumerate(temperatures)], key=lambda x: x[0] * n + x[1])
        result = [0] * n
        for i, cur in enumerate(arr):
            cur_temp, cur_index = cur
            if i == n - 1:
                result[cur_index] = 0
                continue
            min_index = None
            for fut_temp, fut_index in arr[i + 1:]:
                if fut_temp > cur_temp and fut_index > cur_index:
                    if min_index is None or min_index > fut_index:
                        min_index = fut_index
            result[cur_index] = 0 if min_index is None else min_index - cur_index
        return result

class Solution2:
    def dailyTemperatures(self, temperatures: List[int]) -> List[int]:
        lower_temperatures = []
        ans = [0] * len(temperatures)
        for index, temp in enumerate(temperatures):
            if len(lower_temperatures) and lower_temperatures[-1][1] < temp:
                while len(lower_temperatures) and lower_temperatures[-1][1] < temp:
                    past_index, past_temp = lower_temperatures.pop()
                    ans[past_index] = index - past_index
            lower_temperatures.append([index, temp])
        return ans

sol = Solution()
# print(sol.dailyTemperatures([73,74,75,71,69,72,76,73]))
print(sol.dailyTemperatures([89,62,70,58,47,47,46,76,100,70]))