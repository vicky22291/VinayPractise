"""
URL: https://leetcode.com/problems/permutations/description/

Given an array nums of distinct integers, return all the possible permutations. You can return the answer in any order.



Example 1:

Input: nums = [1,2,3]
Output: [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]
Example 2:

Input: nums = [0,1]
Output: [[0,1],[1,0]]
Example 3:

Input: nums = [1]
Output: [[1]]


Constraints:

1 <= nums.length <= 6
-10 <= nums[i] <= 10
All the integers of nums are unique.
"""
from typing import List, Set


class Solution:
    def permute(self, nums: List[int]) -> List[List[int]]:
        result = []
        n = len(nums)

        def mutate(visited: Set[int], current_combo: List[int], ):
            if len(current_combo) == n:
                result.append(current_combo.copy())
                return
            for i in range(n):
                if i not in visited:
                    visited.add(i)
                    current_combo.append(nums[i])
                    mutate(visited, current_combo)
                    current_combo.pop()
                    visited.remove(i)

        mutate(set(), [])
        return result
