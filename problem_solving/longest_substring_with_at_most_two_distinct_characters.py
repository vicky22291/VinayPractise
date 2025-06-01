"""
URL: https://leetcode.com/problems/longest-substring-with-at-most-two-distinct-characters
"""
from collections import defaultdict


class Solution:
    def lengthOfLongestSubstringTwoDistinct(self, s: str) -> int:
        count_of_char = defaultdict(int)
        st = 0
        max_length = 0
        for e in range(len(s)):
            char = s[e]
            count_of_char[char] += 1
            while len(count_of_char) > 2:
                count_of_char[s[st]] -= 1
                if count_of_char[s[st]] == 0:
                    count_of_char.pop(s[st])
                st += 1
            max_length = max(max_length, e - st + 1)
        return max_length