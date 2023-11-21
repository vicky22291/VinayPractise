"""
    Problem: https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/709/greedy/4560/
"""


class Solution:
    def maximum69Number(self, num: int) -> int:
        charArray = list(str(num))
        for i in range(len(charArray)):
            if charArray[i] == '6':
                charArray[i] = '9'
                return int("".join(charArray))
        return num