"""
URL: https://leetcode.com/problems/number-of-connected-components-in-an-undirected-graph/description/

You have a graph of n nodes. You are given an integer n and an array edges where edges[i] = [ai, bi] indicates that there is an edge between ai and bi in the graph.

Return the number of connected components in the graph.



Example 1:


Input: n = 5, edges = [[0,1],[1,2],[3,4]]
Output: 2
Example 2:


Input: n = 5, edges = [[0,1],[1,2],[2,3],[3,4]]
Output: 1


Constraints:

1 <= n <= 2000
1 <= edges.length <= 5000
edges[i].length == 2
0 <= ai <= bi < n
ai != bi
There are no repeated edges.
"""
from collections import defaultdict
from typing import List


class Solution:
    def countComponents(self, n: int, edges: List[List[int]]) -> int:
        adjList, visited = defaultdict(list), set()
        for x, y in edges:
            adjList[x].append(y)
            adjList[y].append(x)
        def dfs(x):
            visited.add(x)
            for y in adjList[x]:
                if y not in visited:
                    dfs(y)
        number_of_components = 0
        for i in range(n):
            if i not in visited:
                number_of_components += 1
                dfs(i)
        return number_of_components