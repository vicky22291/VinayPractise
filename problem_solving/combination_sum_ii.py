"""
URL: https://leetcode.com/problems/combination-sum-ii
"""
import copy
from typing import List

"""
Backtracking is the way to solve this problem. But the use of set is doubtful here.
"""
class Solution:
    def combinationSum2(self, candidates: List[int], target: int) -> List[List[int]]:
        cs, ans, seen = sorted(candidates), [], set()

        def dfs(so_far: List[int], t: int, i: int):
            nonlocal ans, cs, seen
            if cs[i] == t:
                so_far.append(cs[i])
                ans.append(copy.copy(so_far))
                so_far.pop()
                return
            if cs[i] > t:
                return
            so_far.append(cs[i])
            t_so_far = tuple(so_far)
            if t_so_far not in seen:
                seen.add(t_so_far)
                dfs(so_far, t - cs[i], i + 1)
            so_far.pop()
            # This has to be after the above code only because of seen all single elements are exhausted first and then there is no further iteration.
            dfs(so_far, t, i + 1)

        dfs([], target, 0)
        return ans

"""
Instead of above the better iteration is to use loop from index to len.
For every element we track in so_far continue to next and break where it is not possible.
remove the element from tracking in so_far. This way the seen set is not required.
"""

class Solution2:
    def combinationSum2(self, candidates: List[int], target: int) -> List[List[int]]:
        cs, ans, n = sorted(candidates), [], len(candidates)

        def backtracking(so_far: List[int], t: int, index: int):
            nonlocal cs, ans, n
            if t == 0:
                ans.append(so_far.copy())
            elif t < 0:
                return
            else:
                for i in range(index, n):
                    if i > index and cs[i] == cs[i - 1]:
                        continue
                    if t < cs[i]:
                        break
                    so_far.append(cs[i])
                    backtracking(so_far, t - cs[i], i + 1)
                    so_far.pop()

        backtracking([], target, 0)
        return ans
sol = Solution2()
print(sol.combinationSum2([10,1,2,7,6,1,5], 8))