import bisect
from typing import List


"""
    https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/710/binary-search/4574/
"""


class Solution:
    def answerQueries(self, nums: List[int], queries: List[int]) -> List[int]:
        nums = sorted(nums)
        for i in range(1, len(nums)):
            nums[i] += nums[i - 1]

        return [bisect.bisect_right(nums, query) for query in queries]