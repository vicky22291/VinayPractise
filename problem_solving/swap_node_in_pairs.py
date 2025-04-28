"""
URL: https://leetcode.com/problems/swap-nodes-in-pairs/

Given a linked list, swap every two adjacent nodes and return its head. You must solve the problem without modifying the values in the list's nodes (i.e., only nodes themselves may be changed.)



Example 1:

Input: head = [1,2,3,4]

Output: [2,1,4,3]

Explanation:



Example 2:

Input: head = []

Output: []

Example 3:

Input: head = [1]

Output: [1]

Example 4:

Input: head = [1,2,3]

Output: [2,1,3]



Constraints:

The number of nodes in the list is in the range [0, 100].
0 <= Node.val <= 100
"""
from typing import Optional


# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
class Solution:
    def swapPairs(self, head: Optional[ListNode]) -> Optional[ListNode]:
        if head is None or head.next is None:
            return head
        first = second = new_head = last_update = None
        node = head
        while node:
            if first is None:
                first = node
            elif second is None:
                second = node
            else:
                first.next, second.next = node, first
                if new_head is None:
                    new_head = second
                if last_update:
                    last_update.next = second
                first, second, last_update = node, None, first
            node = node.next
        if first and second:
            first.next, second.next = None, first
            if new_head is None:
                new_head = second
            if last_update:
                    last_update.next = second
        return new_head