import collections


"""
    https://leetcode.com/problems/reverse-string-ii/
"""


class Solution:
    def reverseStr(self, s: str, k: int) -> str:
        ans = []
        for i, char in enumerate(s):
            if i % k == 0:
                ans.append(collections.deque())
            if i // k % 2:
                ans[-1].append(char)
            else:
                ans[-1].appendleft(char)
        return "".join(["".join(chars) for chars in ans])


