"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/127/strings/885/
"""


class Solution(object):
    def strStr(self, haystack, needle):
        h, n = len(haystack), len(needle)
        for i in range(h):
            if i + n <= h and haystack[i:i+n] == needle:
                return i
        return -1