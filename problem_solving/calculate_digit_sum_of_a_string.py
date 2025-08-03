"""
URL: https://leetcode.com/problems/calculate-digit-sum-of-a-string/?envType=company&envId=uber&favoriteSlug=uber-all
"""


class Solution:
    def digitSum(self, s: str, k: int) -> str:
        n = len(s)
        if n <= k:
            return s
        nextString = ""
        i = 0
        while i < n:
            ss = s[i:i+k]
            sd = 0
            for char in ss:
                sd += int(char)
            nextString += str(sd)
            i += k
        return self.digitSum(nextString, k)