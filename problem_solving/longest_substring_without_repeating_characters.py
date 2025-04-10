"""
URL: https://leetcode.com/explore/interview/card/facebook/5/array-and-strings/3008/

Given a string s, find the length of the longest substring without duplicate characters.



Example 1:

Input: s = "abcabcbb"
Output: 3
Explanation: The answer is "abc", with the length of 3.
Example 2:

Input: s = "bbbbb"
Output: 1
Explanation: The answer is "b", with the length of 1.
Example 3:

Input: s = "pwwkew"
Output: 3
Explanation: The answer is "wke", with the length of 3.
Notice that the answer must be a substring, "pwke" is a subsequence and not a substring.


Constraints:

0 <= s.length <= 5 * 104
s consists of English letters, digits, symbols and spaces.
"""
from collections import Counter


class Solution:
    def solve(self, input_string: str):
        chars = Counter()
        n = len(input_string)
        start = end = 0
        result = 0
        while end < n:
            char = input_string[end]
            chars[char] += 1
            while chars[char] > 1:
                old_char = input_string[start]
                chars[old_char] -= 1
                start += 1
            result = max(result, end - start + 1)
            end += 1
        return result

solution = Solution()
print(solution.solve("abcabcbb"))
print(solution.solve("bbbbb"))
print(solution.solve("pwwkew"))