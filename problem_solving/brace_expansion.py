"""
URL: https://leetcode.com/problems/brace-expansion
"""
from typing import List


class Solution:
    def expand(self, s: str) -> List[str]:
        subs = []
        for sub1 in s.split('{'):
            for sub2 in sub1.split('}'):
                subs.append(sorted(sub2.split(',')))
        ans = []
        for val in subs:
            nextAns = []
            if len(ans) == 0:
                for string in val:
                    if string != '':
                        nextAns.append(string)
            else:
                for earlierString in ans:
                    for string in val:
                        nextAns.append(earlierString + string)
            ans = nextAns
        return ans

sol = Solution()
print(sol.expand("{a,b,c}d{e,f}"))