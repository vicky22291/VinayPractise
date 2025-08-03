"""
https://leetcode.com/problems/excel-sheet-column-number/?envType=company&envId=uber&favoriteSlug=uber-all
"""


class Solution:
    def titleToNumber(self, columnTitle: str) -> int:
        ans = 0
        for char in columnTitle:
            ans = ans * 26 + ord(char) - ord('A') + 1
        return ans