from typing import List


"""
    Problem: https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/707/traversals-trees-graphs/4629/
    Using BFS
"""


class Solution:
    def reachableNodes(self, n: int, edges: List[List[int]], restricted: List[int]) -> int:
        if 0 in restricted:
            return 0
        seen = set(restricted)
        adjacencies = [[] for _ in range(n)]
        for x, y in edges:
            adjacencies[x].append(y)
            adjacencies[y].append(x)
        count = 1
        seen.add(0)
        curQ = [0]
        nxtQ = []
        while curQ:
            x = curQ.pop()
            for y in adjacencies[x]:
                if y not in seen:
                    seen.add(y)
                    count += 1
                    nxtQ.append(y)
            if not curQ:
                curQ, nxtQ = nxtQ, curQ
        return count