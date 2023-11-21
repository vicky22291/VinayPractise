"""
    https://leetcode.com/problems/strobogrammatic-number/
"""


class Solution:
    def isStrobogrammatic(self, num: str) -> bool:
        pairs = {
            '1': '1',
            '8': '8',
            '0': '0',
            '6': '9',
            '9': '6'
        }
        left = 0
        right = len(num) - 1
        while left <= right:
            if num[left] not in pairs or \
                    (left == right and num[left] not in ['0', '1', '8']) or \
                    num[right] != pairs[num[left]]:
                return False
            left += 1
            right -= 1
        return True