"""
URL: https://leetcode.com/problems/merge-strings-alternately/description
"""


class Solution:
    def mergeAlternately(self, word1: str, word2: str) -> str:
        i, n1, n2, ans = 0, len(word1), len(word2), []
        while i < min(n1, n2):
            ans.append(word1[i])
            ans.append(word2[i])
            i += 1
        if i < n1:
            return "".join(ans) + word1[i:]
        elif i < n2:
            return "".join(ans) + word2[i:]
        else:
            return "".join(ans)