"""
    https://leetcode.com/problems/count-good-meals/description/
"""
from typing import List
import collections


class Solution:
    def countPairs(self, deliciousness: List[int]) -> int:
        group_by_deliciousness = collections.Counter(deliciousness)
        keys = sorted(list(group_by_deliciousness.keys()))
        size, tot = len(keys), 0
        prev_power, curr_power, upper_bound = .5, 1, keys[-1] << 1
        while curr_power <= upper_bound:
            for j in range(size):
                cnt = group_by_deliciousness[keys[j]]
                if keys[j] < prev_power:
                    tot += cnt * group_by_deliciousness[curr_power - keys[j]]
                elif keys[j] == prev_power:
                    tot += (cnt * (cnt - 1)) >> 1
                else:
                    break
            prev_power, curr_power = curr_power, curr_power << 1
        return tot % 1_000_000_007