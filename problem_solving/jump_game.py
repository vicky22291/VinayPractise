from typing import List


class Solution:
    def canJump(self, nums: List[int]) -> bool:
        def sub_jump(i: int) -> bool:
            if i == 0:
                return True
            for j in range(i - 1, -1, -1):
                if nums[j] >= i - j:
                    if sub_jump(j):
                        return True
            return False
        return sub_jump(len(nums) - 1)


class Solution1:
    def canJump(self, nums: List[int]) -> bool:
        n = len(nums)
        dp = [False] * n
        dp[0] = True
        for i, num in enumerate(nums):
            dp[i + 1:min(i + num + 1, n)] = [True] * (min(i + num + 1, n) - i - 1)
            if dp[n - 1]:
                return True
        return dp[n - 1]

class Solution2:
    def canJump(self, nums: List[int]) -> bool:
        lastPos = len(nums) - 1
        for i in range(len(nums) - 1, -1, -1):
            if i + nums[i] >= lastPos:
                lastPos = i
        return lastPos == 0

sol = Solution2()
print(sol.canJump([2,0,6,9,8,4,5,0,8,9,1,2,9,6,8,8,0,6,3,1,2,2,1,2,6,5,3,1,2,2,6,4,2,4,3,0,0,0,3,8,2,4,0,1,2,0,1,4,6,5,8,0,7,9,3,4,6,6,5,8,9,3,4,3,7,0,4,9,0,9,8,4,3,0,7,7,1,9,1,9,4,9,0,1,9,5,7,7,1,5,8,2,8,2,6,8,2,2,7,5,1,7,9,6]))