"""
URL: https://leetcode.com/problems/palindrome-permutation/description/?envType=company&envId=uber&favoriteSlug=uber-all
"""
from collections import Counter


class Solution:
    def canPermutePalindrome(self, s: str) -> bool:
        count = Counter(s)
        alreadySeen1 = False
        for val in count.values():
            if val % 2:
                if not alreadySeen1:
                    alreadySeen1 = True
                else:
                    return False
        return True