"""
URL: https://leetcode.com/problems/number-of-recent-calls
"""
from collections import deque


class RecentCounter:

    def __init__(self):
        self.requests = deque()

    def ping(self, t: int) -> int:
        while len(self.requests) and self.requests[0] + 3000 < t:
            self.requests.popleft()
        self.requests.append(t)
        return len(self.requests)