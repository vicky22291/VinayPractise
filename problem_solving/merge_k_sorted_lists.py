"""
URL: https://leetcode.com/problems/merge-k-sorted-lists/

You are given an array of k linked-lists lists, each linked-list is sorted in ascending order.

Merge all the linked-lists into one sorted linked-list and return it.



Example 1:

Input: lists = [[1,4,5],[1,3,4],[2,6]]
Output: [1,1,2,3,4,4,5,6]
Explanation: The linked-lists are:
[
  1->4->5,
  1->3->4,
  2->6
]
merging them into one sorted list:
1->1->2->3->4->4->5->6
Example 2:

Input: lists = []
Output: []
Example 3:

Input: lists = [[]]
Output: []


Constraints:

k == lists.length
0 <= k <= 104
0 <= lists[i].length <= 500
-104 <= lists[i][j] <= 104
lists[i] is sorted in ascending order.
The sum of lists[i].length will not exceed 104.
"""
from heapq import heappush, heappop
from typing import List, Optional


# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
class Solution:
    def mergeKLists(self, lists: List[Optional[ListNode]]) -> Optional[ListNode]:
        class Node:
            def __init__(self, facadeTo: ListNode):
                self.facadeTo = facadeTo
            def __lt__(self, other):
                return self.facadeTo.val < other.facadeTo.val
        mins, final_head, prev = [], None, None
        for head in lists:
            if head:
                heappush(mins, Node(head))
        while len(mins):
            node = heappop(mins)
            if final_head is None:
                final_head = node.node
            if prev:
                prev.next = node.node
            if node.node.next:
                heappush(mins, Node(node.next))
            prev = node.node
        return final_head
