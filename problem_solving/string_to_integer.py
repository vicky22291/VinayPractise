"""
URL: https://leetcode.com/explore/interview/card/facebook/5/array-and-strings/3009/

Implement the myAtoi(string s) function, which converts a string to a 32-bit signed integer.

The algorithm for myAtoi(string s) is as follows:

Whitespace: Ignore any leading whitespace (" ").
Signedness: Determine the sign by checking if the next character is '-' or '+', assuming positivity if neither present.
Conversion: Read the integer by skipping leading zeros until a non-digit character is encountered or the end of the string is reached. If no digits were read, then the result is 0.
Rounding: If the integer is out of the 32-bit signed integer range [-231, 231 - 1], then round the integer to remain in the range. Specifically, integers less than -231 should be rounded to -231, and integers greater than 231 - 1 should be rounded to 231 - 1.
Return the integer as the final result.



Example 1:

Input: s = "42"

Output: 42

Explanation:

The underlined characters are what is read in and the caret is the current reader position.
Step 1: "42" (no characters read because there is no leading whitespace)
         ^
Step 2: "42" (no characters read because there is neither a '-' nor '+')
         ^
Step 3: "42" ("42" is read in)
           ^
Example 2:

Input: s = " -042"

Output: -42

Explanation:

Step 1: "   -042" (leading whitespace is read and ignored)
            ^
Step 2: "   -042" ('-' is read, so the result should be negative)
             ^
Step 3: "   -042" ("042" is read in, leading zeros ignored in the result)
               ^
Example 3:

Input: s = "1337c0d3"

Output: 1337

Explanation:

Step 1: "1337c0d3" (no characters read because there is no leading whitespace)
         ^
Step 2: "1337c0d3" (no characters read because there is neither a '-' nor '+')
         ^
Step 3: "1337c0d3" ("1337" is read in; reading stops because the next character is a non-digit)
             ^
Example 4:

Input: s = "0-1"

Output: 0

Explanation:

Step 1: "0-1" (no characters read because there is no leading whitespace)
         ^
Step 2: "0-1" (no characters read because there is neither a '-' nor '+')
         ^
Step 3: "0-1" ("0" is read in; reading stops because the next character is a non-digit)
          ^
Example 5:

Input: s = "words and 987"

Output: 0

Explanation:

Reading stops at the first non-digit character 'w'.



Constraints:

0 <= s.length <= 200
s consists of English letters (lower-case and upper-case), digits (0-9), ' ', '+', '-', and '.'.
"""


class Solution:
    def myAtoi(self, s: str) -> int:
        sign = 1
        final_result = 0
        stage1_completed = False
        stage2_completed = False
        stage3_completed = False
        for index, char in enumerate(s):
            if not stage1_completed and char == " ":
                continue
            elif not stage2_completed and char in ['-', '+']:
                stage1_completed = True
                stage2_completed = True
                sign = -1 if char == '-' else 1
            elif not stage3_completed and char == '0':
                stage1_completed = True
                stage2_completed = True
                continue
            elif char in "0123456789":
                stage1_completed = True
                stage2_completed = True
                stage3_completed = True
                final_result = final_result * 10 + int(char)
            else:
                break
        final_result *= sign
        if final_result < -pow(2, 31):
            final_result = -pow(2, 31)
        elif final_result > pow(2, 31) - 1:
            final_result = pow(2, 31) - 1
        return final_result

sol = Solution()
print(sol.myAtoi("42"))
print(sol.myAtoi("-042"))
print(sol.myAtoi("1337c0d3"))