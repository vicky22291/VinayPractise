"""
    https://leetcode.com/problems/pancake-sorting/
"""
from typing import List


class Solution:
    def pancakeSort(self, arr: List[int]) -> List[int]:
        def flip(sublist, k):
            i = 0
            while i < k / 2:
                sublist[i], sublist[k-i-1] = sublist[k-i-1], sublist[i]
                i += 1

        ans = []
        value_to_sort = len(arr)
        while value_to_sort > 0:
            # locate the position for the value to sort in this round
            index = arr.index(value_to_sort)

            # sink the value_to_sort to the bottom,
            #   with at most two steps of pancake flipping.
            if index != value_to_sort - 1:
                # flip the value to the head if necessary
                if index != 0:
                    ans.append(index+1)
                    flip(arr, index+1)
                # now that the value is at the head, flip it to the bottom
                ans.append(value_to_sort)
                flip(arr, value_to_sort)

            # move on to the next round
            value_to_sort -= 1

        return ans