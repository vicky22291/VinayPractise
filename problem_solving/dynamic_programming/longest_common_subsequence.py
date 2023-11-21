from functools import cache


"""
class Solution:
    def longestCommonSubsequence(self, text1: str, text2: str) -> int:
        m = len(text1)
        n = len(text2)

        @cache
        def dp(i, j):
            nonlocal text1, text2
            if i == 0 or j == 0:
                return 0
            if text1[i - 1] == text2[j - 1]:
                return dp(i - 1, j - 1) + 1
            else:
                return max(dp(i - 1, j), dp(i, j - 1))

        return dp(m, n)
"""


"""
class Solution:
    def longestCommonSubsequence(self, text1: str, text2: str) -> int:
        m = len(text1)
        n = len(text2)

        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(m):
            for j in range(n):
                if text1[i] == text2[j]:
                    dp[i + 1][j + 1] = dp[i][j] + 1
                else:
                    dp[i + 1][j + 1] = max(dp[i][j + 1], dp[i + 1][j])

        return dp[-1][-1]
"""


class Solution:
    def longestCommonSubsequence(self, text1: str, text2: str) -> int:
        m = len(text1)
        n = len(text2)

        pdp = [0] * (n + 1)
        cdp = None
        for i in range(m):
            cdp = [0] * (n + 1)
            for j in range(n):
                if text1[i] == text2[j]:
                    cdp[j + 1] = pdp[j] + 1
                else:
                    cdp[j + 1] = max(pdp[j + 1], cdp[j])
            pdp = cdp

        return cdp[-1]