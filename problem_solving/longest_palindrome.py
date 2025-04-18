"""
URL: https://leetcode.com/problems/longest-palindrome/description/

Given a string s which consists of lowercase or uppercase letters, return the length of the longest palindrome that can be built with those letters.

Letters are case sensitive, for example, "Aa" is not considered a palindrome.



Example 1:

Input: s = "abccccdd"
Output: 7
Explanation: One longest palindrome that can be built is "dccaccd", whose length is 7.
Example 2:

Input: s = "a"
Output: 1
Explanation: The longest palindrome that can be built is "a", whose length is 1.


Constraints:

1 <= s.length <= 2000
s consists of lowercase and/or uppercase English letters only.
"""
from collections import Counter


class Solution:
    def longestPalindrome(self, s: str) -> int:
        count_s = Counter(s)
        result = 0
        odd_greater_than_1 = False
        for val in count_s.values():
            q, r = val // 2, val % 2
            if r:
                odd_greater_than_1 = True
            result += 2 * q
        return result + 1 if odd_greater_than_1 else result