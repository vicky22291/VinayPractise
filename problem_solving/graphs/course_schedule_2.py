"""
    https://leetcode.com/explore/interview/card/top-interview-questions-hard/118/trees-and-graphs/848/
"""


class Solution(object):
    def __init__(self):
        self.already_computed = []

    def __addToAdjacency(self, course, adjacency_list, parent):
        if course in parent:
            return None
        if course in self.already_computed:
            return adjacency_list[course]
        parent.add(course)
        current_courses_dependencies = list(adjacency_list[course])
        for i in current_courses_dependencies:
            children = self.__addToAdjacency(i, adjacency_list, parent)
            if children is None:
                return None
            for child in children:
                adjacency_list[course].add(child)
        parent.remove(course)
        self.already_computed.append(course)
        return adjacency_list[course]

    def findOrder(self, numCourses, prerequisites):
        """
        :type numCourses: int
        :type prerequisites: List[List[int]]
        :rtype: bool
        """
        self.already_computed = []
        adjacency_list = {}
        for i in range(numCourses):
            adjacency_list[i] = set()
        for edge in prerequisites:
            adjacency_list[edge[0]].add(edge[1])
        for i in range(numCourses):
            children = self.__addToAdjacency(i, adjacency_list, set())
            if children is None:
                return []
        return self.already_computed
