"""
URL: https://leetcode.com/problems/course-schedule/description/

There are a total of numCourses courses you have to take, labeled from 0 to numCourses - 1. You are given an array prerequisites where prerequisites[i] = [ai, bi] indicates that you must take course bi first if you want to take course ai.

For example, the pair [0, 1], indicates that to take course 0 you have to first take course 1.
Return true if you can finish all courses. Otherwise, return false.



Example 1:

Input: numCourses = 2, prerequisites = [[1,0]]
Output: true
Explanation: There are a total of 2 courses to take.
To take course 1 you should have finished course 0. So it is possible.
Example 2:

Input: numCourses = 2, prerequisites = [[1,0],[0,1]]
Output: false
Explanation: There are a total of 2 courses to take.
To take course 1 you should have finished course 0, and to take course 0 you should also have finished course 1. So it is impossible.


Constraints:

1 <= numCourses <= 2000
0 <= prerequisites.length <= 5000
prerequisites[i].length == 2
0 <= ai, bi < numCourses
All the pairs prerequisites[i] are unique.
"""
from collections import defaultdict
from typing import List


class Solution:
    def canFinish(self, numCourses: int, prerequisites: List[List[int]]) -> bool:
        adj_list = defaultdict(list)
        indegrees = defaultdict(int)
        zeroes = set()
        for fro, to in prerequisites:
            if indegrees[fro] == 0:
                zeroes.add(fro)
            if to in zeroes:
                zeroes.remove(to)
            adj_list[fro].append(to)
            indegrees[to] += 1
        processed = 0
        while len(zeroes):
            element = zeroes.pop()
            for to in adj_list[element]:
                indegrees[to] -= 1
                if indegrees[to] == 0:
                    zeroes.add(to)
            processed += 1
        return processed == len(adj_list)
