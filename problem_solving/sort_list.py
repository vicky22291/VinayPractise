"""
URL: https://leetcode.com/problems/sort-list/

Given the head of a linked list, return the list after sorting it in ascending order.



Example 1:


Input: head = [4,2,1,3]
Output: [1,2,3,4]
Example 2:


Input: head = [-1,5,3,4,0]
Output: [-1,0,3,4,5]
Example 3:

Input: head = []
Output: []


Constraints:

The number of nodes in the list is in the range [0, 5 * 104].
-105 <= Node.val <= 105


Follow up: Can you sort the linked list in O(n logn) time and O(1) memory (i.e. constant space)?
"""
from typing import Optional


# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Solution:
    def sortList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        if head is None:
            return None
        node, arr = head, []
        while node:
            arr.append(node)
            node = node.next
        arr = sorted(arr, key=lambda x: x.val)
        new_head = None
        prev = None
        for node in arr:
            if new_head is None:
                new_head = node
            if prev:
                prev.next = node
            prev = node
        prev.next = None
        return new_head