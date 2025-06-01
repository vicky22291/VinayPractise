"""
URL: https://leetcode.com/problems/palindromic-substrings
"""
class Solution:
    def countSubstrings(self, s: str) -> int:
        ans, n = 0, len(s)

        def expand(left, right):
            nonlocal ans, s
            while left >= 0 and right < n and s[left] == s[right]:
                ans += 1
                left -= 1
                right += 1

        for i in [1, 2]:
            for j in range(len(s) - i + 1):
                expand(j, j + i - 1)
        return ans

sol = Solution()
print(sol.countSubstrings("abc"))