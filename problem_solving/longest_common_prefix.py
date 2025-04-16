"""
URL:

Write a function to find the longest common prefix string amongst an array of strings.

If there is no common prefix, return an empty string "".



Example 1:

Input: strs = ["flower","flow","flight"]
Output: "fl"
Example 2:

Input: strs = ["dog","racecar","car"]
Output: ""
Explanation: There is no common prefix among the input strings.


Constraints:

1 <= strs.length <= 200
0 <= strs[i].length <= 200
strs[i] consists of only lowercase English letters if it is non-empty.
"""
from typing import List


class Solution:
    def longestCommonPrefix(self, strs: List[str]) -> str:
        n = min([len(s) for s in strs])
        result = ""
        for i in range(n):
            cur_char = None
            for s in strs:
                if cur_char is None:
                    cur_char = s[i]
                if cur_char != s[i]:
                    return result
            result += cur_char
        return result