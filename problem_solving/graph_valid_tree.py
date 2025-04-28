"""
URL: https://leetcode.com/problems/graph-valid-tree/

You have a graph of n nodes labeled from 0 to n - 1. You are given an integer n and a list of edges where edges[i] = [ai, bi] indicates that there is an undirected edge between nodes ai and bi in the graph.

Return true if the edges of the given graph make up a valid tree, and false otherwise.



Example 1:


Input: n = 5, edges = [[0,1],[0,2],[0,3],[1,4]]
Output: true
Example 2:


Input: n = 5, edges = [[0,1],[1,2],[2,3],[1,3],[1,4]]
Output: false


Constraints:

1 <= n <= 2000
0 <= edges.length <= 5000
edges[i].length == 2
0 <= ai, bi < n
ai != bi
There are no self-loops or repeated edges.
"""
from collections import defaultdict
from typing import List


class Solution:
    def validTree(self, n: int, edges: List[List[int]]) -> bool:
        if len(edges) == 0 and n == 1:
            return True
        if len(edges) != n - 1:
            return False
        adjList, incoming = defaultdict(list), defaultdict(int)
        for to, fro in edges:
            adjList[to].append(fro)
            adjList[fro].append(to)
            incoming[fro] += 1
            incoming[to] += 1
        for i in range(n):
            if incoming[i] == 0:
                return False
        queue, next_queue = [], []
        for i in range(n):
            if incoming[i] == 1:
                queue.append(i)
        while len(queue):
            cur = queue.pop()
            incoming[cur] -= 1
            for i in adjList[cur]:
                incoming[i] -= 1
                if incoming[i] == 1:
                    next_queue.append(i)
            if len(queue) == 0:
                queue, next_queue = next_queue, queue
        for i in range(n):
            if incoming[i] > 0:
                return False
        return True
