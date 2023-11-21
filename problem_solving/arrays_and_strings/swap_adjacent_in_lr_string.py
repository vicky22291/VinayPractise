"""
    https://leetcode.com/problems/swap-adjacent-in-lr-string/description/
"""
class Solution:
    def canTransform(self, start: str, end: str) -> bool:
        n = len(start)
        i = j = 0
        while i < n or j < n:
            while i < n and start[i] == 'X':
                i += 1
            while j < n and end[j] == "X":
                j += 1
            if n in (i,j):
                return i == j == n
            if start[i] != end[j]:
                return False
            if start[i] == 'L':
                if i < j:
                    return False
            else:
                if i > j:
                    return False
            i += 1
            j += 1
        return True