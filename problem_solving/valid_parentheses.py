"""
URL: https://leetcode.com/problems/valid-parentheses/description/

Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.

An input string is valid if:

Open brackets must be closed by the same type of brackets.
Open brackets must be closed in the correct order.
Every close bracket has a corresponding open bracket of the same type.


Example 1:

Input: s = "()"

Output: true

Example 2:

Input: s = "()[]{}"

Output: true

Example 3:

Input: s = "(]"

Output: false

Example 4:

Input: s = "([])"

Output: true



Constraints:

1 <= s.length <= 104
s consists of parentheses only '()[]{}'.
"""


class Solution:
    def isValid(self, s: str) -> bool:
        open_braces = {
            '(': ')',
            '{': '}',
            '[': ']'
        }
        close_braces = {value: key for key, value in open_braces.items()}
        stack = []
        for index, char in enumerate(s):
            if char in open_braces:
                stack.append(char)
            elif len(stack) and stack[-1] == close_braces[char]:
                stack.pop(-1)
            else:
                return False
        return False if len(stack) else True