"""
URL: https://leetcode.com/problems/maximum-product-subarray/

Given an integer array nums, find a subarray that has the largest product, and return the product.

The test cases are generated so that the answer will fit in a 32-bit integer.



Example 1:

Input: nums = [2,3,-2,4]
Output: 6
Explanation: [2,3] has the largest product 6.
Example 2:

Input: nums = [-2,0,-1]
Output: 0
Explanation: The result cannot be 2, because [-2,-1] is not a subarray.


Constraints:

1 <= nums.length <= 2 * 104
-10 <= nums[i] <= 10
The product of any subarray of nums is guaranteed to fit in a 32-bit integer.
"""
from bisect import bisect_right, bisect_left
from math import prod
from typing import List


class Solution:
    def maxProduct(self, nums: List[int]) -> int:
        only_positives, negatives, start = [], [], 0
        for i, num in enumerate(nums):
            if num > 0:
                only_positives.append([start, i])
            else:
                if start != i:
                    only_positives.append([start, i - 1])
                if num < 0:
                    negatives.append(i)
                start = i + 1
        n, visited = len(negatives), set()
        if n >= 2:
            i = 0
            while i < n - 1:
                if negatives[i + 1] - negatives[i] == 1:
                    new_insertion = bisect_right(only_positives, negatives[i], key=lambda x: x[1])
                    only_positives.insert(new_insertion, [negatives[i], negatives[i + 1]])
                    i += 2
                    visited.add(i)
                    visited.add(i + 1)
                else:
                    i += 1
            if len(only_positives):
                i = 0
                while i < n - 1:
                    if i not in visited and i + 1 not in visited:
                        probable = bisect_left(only_positives, negatives[i], key=lambda x: x[0])
                        start, end = only_positives[probable]
                        if negatives[i + 1] == end + 1 and negatives[i] == start - 1:
                            only_positives[probable] = [negatives[i], negatives[i + 1]]
                            i += 2
                        else:
                            i += 1
                    else:
                        i += 1
        if len(only_positives) == 0:
            return max(nums)
        final = []
        for start, end in only_positives:
            if len(final) == 0:
                final.append([start, end])
            elif final[-1][-1] + 1 == start:
                final[-1][-1] = end
            else:
                final.append([start, end])
        max_product = -1_000_000_000
        for start, end in final:
            max_product = max(max_product, prod(nums[start:end + 1]))
        return max_product

class Solution2:
    def maxProduct(self, nums):
        if len(nums) == 0:
            return 0

        max_so_far = nums[0]
        min_so_far = nums[0]
        result = max_so_far

        for i in range(1, len(nums)):
            curr = nums[i]
            temp_max = max(curr, max(max_so_far * curr, min_so_far * curr))
            min_so_far = min(curr, min(max_so_far * curr, min_so_far * curr))

            # Update max_so_far after updates to min_so_far to avoid overwriting it
            max_so_far = temp_max
            # Update the result with the maximum product found so far
            result = max(max_so_far, result)

        return result

sol = Solution()
# print(sol.maxProduct([-2,0,-1]))
# print(sol.maxProduct([-3,-1,-1]))
print(sol.maxProduct([-2,-3,7]))