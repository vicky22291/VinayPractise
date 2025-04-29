"""
URL: https://leetcode.com/problems/find-k-closest-elements/description/

Given a sorted integer array arr, two integers k and x, return the k closest integers to x in the array. The result should also be sorted in ascending order.

An integer a is closer to x than an integer b if:

|a - x| < |b - x|, or
|a - x| == |b - x| and a < b


Example 1:

Input: arr = [1,2,3,4,5], k = 4, x = 3

Output: [1,2,3,4]

Example 2:

Input: arr = [1,1,2,3,4,5], k = 4, x = -1

Output: [1,1,2,3]



Constraints:

1 <= k <= arr.length
1 <= arr.length <= 104
arr is sorted in ascending order.
-104 <= arr[i], x <= 104
"""
from bisect import bisect_left
from typing import List


class Solution:
    def findClosestElements(self, arr: List[int], k: int, x: int) -> List[int]:
        index, n = bisect_left(arr, x), len(arr)
        if index == n:
            index -= 1
        elif arr[index] != x:
            if index != 0 and arr[index] - x >= x - arr[index - 1]:
                index -= 1
        left = right = index
        for i in range(1, k):
            if right == n - 1:
                left -= 1
            elif left == 0:
                right += 1
            elif x - arr[left - 1] > arr[right + 1] - x:
                right += 1
            else:
                left -= 1
        return arr[left:(right + 1)]

sol = Solution()
# print(sol.findClosestElements([1,1,2,3,4,5], 4, -1))
# print(sol.findClosestElements([1], 1, 1))
# print(sol.findClosestElements([0,0,1,2,3,3,4,7,7,8], 3, 5))
# print(sol.findClosestElements([3,5,8,10], 2, 15))
print(sol.findClosestElements([1,3], 1, 2))