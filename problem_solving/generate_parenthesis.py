"""
URL: https://leetcode.com/problems/generate-parentheses/

Given n pairs of parentheses, write a function to generate all combinations of well-formed parentheses.



Example 1:

Input: n = 3
Output: ["((()))","(()())","(())()","()(())","()()()"]
Example 2:

Input: n = 1
Output: ["()"]


Constraints:

1 <= n <= 8
"""
from typing import List


class Solution:
    def generateParenthesis(self, n: int) -> List[str]:
        ans = set()
        def generate(string: str, k: int):
            if k == 1:
                ans.add("()" + string)
                ans.add(string + "()")
                ans.add(f"({string})")
            else:
                generate(f'(){string}', k - 1)
                generate(f'{string}()', k - 1)
                generate(f'({string})', k - 1)
        generate("", n)
        return list(ans)


class Solution2:
    def generateParenthesis(self, n: int) -> List[str]:
        if n == 0:
            return [""]

        answer = []
        for left_count in range(n):
            for left_string in self.generateParenthesis(left_count):
                for right_string in self.generateParenthesis(
                    n - 1 - left_count
                ):
                    answer.append("(" + left_string + ")" + right_string)

        return answer