"""
URL: https://leetcode.com/problems/evaluate-division
"""
from collections import defaultdict
from typing import List


class Solution:
    def calcEquation(self, equations: List[List[str]], values: List[float], queries: List[List[str]]) -> List[float]:
        class Solution:
            def calcEquation(self, equations: List[List[str]], values: List[float], queries: List[List[str]]) -> List[
                float]:
                denom_map = defaultdict(list)

                for eq in equations:
                    denom_map[eq[0]].append(eq[1])
                    denom_map[eq[1]].append(eq[0])

                value_map = defaultdict(lambda: float('inf'))

                for i, eq in enumerate(equations):
                    value_map[(eq[0], eq[1])] = values[i]
                    value_map[(eq[1], eq[0])] = 1 / values[i]

                res = []

                for query in queries:
                    if len(denom_map[query[0]]) == 0 or len(denom_map[query[1]]) == 0:
                        res.append(-1)
                        continue

                    denoms = deque([(denom, value_map[(query[0], denom)]) for denom in denom_map[query[0]]])
                    visited = set()
                    found = False

                    while denoms:
                        denom, curr_val = denoms.popleft()
                        if denom == query[1]:
                            res.append(curr_val)
                            found = True
                            break

                        visited.add(denom)
                        for next_denom in denom_map[denom]:
                            if next_denom not in visited:
                                denoms.append((next_denom, curr_val * value_map[(denom, next_denom)]))

                    if not found:
                        res.append(-1)

                return res