"""
URL: https://leetcode.com/problems/remove-all-adjacent-duplicates-in-string-ii
"""
from collections import Counter


class Solution:
    def removeDuplicates(self, s: str, k: int) -> str:
        st = []
        for c in s:
            if len(st) == 0:
                st.append([c, 1])
            elif st[-1][0] == c:
                st[-1][1] += 1
            else:
                st.append([c, 1])
            if len(st) and st[-1][1] == k:
                st.pop()
        ans = []
        for c, n in st:
            for i in range(n):
                ans.append(c)
        return "".join(ans)

sol = Solution()
print(sol.removeDuplicates("yfttttfbbbbnnnnffbgffffgbbbbgssssgthyyyy", 4))