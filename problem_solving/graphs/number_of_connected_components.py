"""
    Problem: https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/707/traversals-trees-graphs/4670/
    using a Simple BFS
"""


class Solution:
    def countComponents(self, n: int, edges: List[List[int]]) -> int:
        adjacencies = [[] for _ in range(n)]
        for x, y in edges:
            adjacencies[x].append(y)
            adjacencies[y].append(x)
        nComponents = 0
        seen = set()
        for i in range(n):
            if i not in seen:
                nComponents += 1
                curQ = [i]
                nxtQ = []
                while curQ:
                    x = curQ.pop()
                    for y in adjacencies[x]:
                        if y not in seen:
                            nxtQ.append(y)
                            seen.add(y)
                    if not curQ:
                        curQ, nxtQ = nxtQ, curQ
        return nComponents