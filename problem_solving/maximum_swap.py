"""
URL: https://leetcode.com/problems/maximum-swap/description
"""

class Solution:
    def maximumSwap(self, num: int) -> int:
        snum = str(num)
        n = len(snum)
        carray = list(snum)
        rcarray = list(reversed(carray))
        for i in range(n - 1):
            max_element = max(snum[i + 1:])
            if snum[i] < max_element:
                j = n - 1 - rcarray.index(max_element)
                carray[j], carray[i] = carray[i], carray[j]
                return int("".join(carray))
        return num