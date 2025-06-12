"""
URL: https://leetcode.com/problems/basic-calculator-iii/description
"""


class Solution:
    def calculate(self, s: str) -> int:
        def evaluate(x, y, operator):
            if operator == "+":
                return x
            elif operator == "-":
                return -x
            elif operator == "*":
                return x * y
            else:
                return int(x / y)

        stack, curNum, prevOp = [], 0, "+"
        s += "@"

        for c in s:
            if c.isdigit():
                curNum = curNum * 10 + int(c)
            elif c == '(':
                stack.append(prevOp)
                prevOp = "+"
            else:
                if prevOp in "*/":
                    stack.append(evaluate(stack.pop(), curNum, prevOp))
                else:
                    stack.append(evaluate(curNum, 0, prevOp))

                curNum = 0
                prevOp = c
                if c == ')':
                    while type(stack[-1]) == int:
                        curNum += stack.pop()
                    prevOp = stack.pop()
        return sum(stack)



