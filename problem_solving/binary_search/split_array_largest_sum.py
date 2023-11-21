"""
https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/710/binary-search/4573/
"""


from typing import List


class Solution:
    def splitArray(self, nums: List[int], m: int) -> int:
        def min_subarrays_required(max_sum_allowed: int) -> int:
            current_sum = 0
            splits_required = 0

            for element in nums:
                if current_sum + element <= max_sum_allowed:
                    current_sum += element
                else:
                    current_sum = element
                    splits_required += 1

            return splits_required + 1

        left = max(nums)
        right = sum(nums)
        while left <= right:
            max_sum_allowed = (left + right) // 2

            if min_subarrays_required(max_sum_allowed) <= m:
                right = max_sum_allowed - 1
                minimum_largest_split_sum = max_sum_allowed
            else:
                left = max_sum_allowed + 1

        return minimum_largest_split_sum
