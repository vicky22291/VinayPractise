"""
URL: https://leetcode.com/problems/search-in-rotated-sorted-array-ii
"""


class Solution:
    def search(self, nums, target):
        n = len(nums)
        if n == 0:
            return False
        end = n - 1
        start = 0
        while start <= end:
            mid = start + (end - start) // 2
            if nums[mid] == target:
                return True
            if not self.isBinarySearchHelpful(nums, start, nums[mid]):
                start += 1
                continue
            # which array does pivot belong to.
            pivotArray = self.existsInFirst(nums, start, nums[mid])
            # which array does target belong to.
            targetArray = self.existsInFirst(nums, start, target)
            if pivotArray ^ targetArray:
                # if pivot and target exist in different sorted arrays, recall that xor is true
                if pivotArray:
                    start = mid + 1  # pivot in the first, target in the second
                else:
                    end = mid - 1  # target in the first, pivot in the second
            else:  # if pivot and target exist in same sorted array
                if nums[mid] < target:
                    start = mid + 1
                else:
                    end = mid - 1
        return False

    # returns true if we can reduce the search space in current binary search space
    def isBinarySearchHelpful(self, nums, start, element):
        return nums[start] != element

    # returns true if element exists in first array, false if it exists in second
    def existsInFirst(self, nums, start, element):
        return nums[start] <= element