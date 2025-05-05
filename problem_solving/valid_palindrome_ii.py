"""
URL: https://leetcode.com/problems/valid-palindrome-ii/description

Given a string s, return true if the s can be palindrome after deleting at most one character from it.



Example 1:

Input: s = "aba"
Output: true
Example 2:

Input: s = "abca"
Output: true
Explanation: You could delete the character 'c'.
Example 3:

Input: s = "abc"
Output: false


Constraints:

1 <= s.length <= 105
s consists of lowercase English letters.
"""


class Solution:
    def validPalindrome(self, s: str) -> bool:
        if len(s) == 1:
            return True
        left, right, isRemoved = 0, len(s) - 1, False
        while left <= right:
            if s[left] == s[right]:
                left += 1
                right -= 1
            elif not isRemoved and s[left] != s[right]:
                if s[left] == s[right - 1]:
                    left += 1
                    right -= 2
                    isRemoved = True
                elif s[left + 1] == s[right]:
                    left += 2
                    right -= 1
                else:
                    return False
            else:
                return False
        return True


class Solution2:
    def validPalindrome(self, s: str) -> bool:
        def check_palindrome(s, i, j):
            while i < j:
                if s[i] != s[j]:
                    return False
                i += 1
                j -= 1

            return True

        i = 0
        j = len(s) - 1
        while i < j:
            # Found a mismatched pair - try both deletions
            if s[i] != s[j]:
                return check_palindrome(s, i, j - 1) or check_palindrome(s, i + 1, j)
            i += 1
            j -= 1

        return True