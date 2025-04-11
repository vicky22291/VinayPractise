"""
URL: https://leetcode.com/problems/add-binary/description/

Given two binary strings a and b, return their sum as a binary string.



Example 1:

Input: a = "11", b = "1"
Output: "100"
Example 2:

Input: a = "1010", b = "1011"
Output: "10101"


Constraints:

1 <= a.length, b.length <= 104
a and b consist only of '0' or '1' characters.
Each string does not contain leading zeros except for the zero itself.
"""

class Solution:
    def addBinary(self, a: str, b: str) -> str:
        carry = 0
        result = ""
        na = len(a)
        nb = len(b)
        for i in range(1, max(na, nb) + 1):
            ia = 0 if na < i else int(a[-i])
            ib = 0 if nb < i else int(b[-i])
            cur_sum = ia + ib + carry
            r, carry = cur_sum % 2, cur_sum // 2
            result = str(r) + result
        if carry:
            result = "1" + result
        return result


sol = Solution()
print(sol.addBinary("11", "1"))