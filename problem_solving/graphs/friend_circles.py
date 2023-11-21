"""
    https://leetcode.com/explore/interview/card/top-interview-questions-hard/118/trees-and-graphs/846/
"""
from typing import List


class Solution:
    def findCircleNum(self, isConnected: List[List[int]]) -> int:
        n = len(isConnected)
        adjList = {i: [] for i in range(1, n + 1)}

        for i in range(len(isConnected)):
            for j in range(len(isConnected)):
                if (isConnected[i][j] == 1 and (i != j)):
                    adjList[i + 1].append(j + 1)

        visited = [False] * (n + 1)
        noOfProvinces = 0

        for city in range(1, n + 1):
            if visited[city] == False:
                self.bfs(adjList, city, visited)
                noOfProvinces += 1

        return noOfProvinces

    def bfs(self, adjList, s, visited):
        queue = collections.deque()
        queue.append(s)
        visited[s] = True
        while queue:
            node = queue.popleft()
            for nei in adjList[node]:
                if (visited[nei] == False):
                    visited[nei] = True
                    queue.append(nei)