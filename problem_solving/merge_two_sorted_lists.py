"""
URL: https://leetcode.com/problems/merge-two-sorted-lists/description/

You are given the heads of two sorted linked lists list1 and list2.

Merge the two lists into one sorted list. The list should be made by splicing together the nodes of the first two lists.

Return the head of the merged linked list.



Example 1:


Input: list1 = [1,2,4], list2 = [1,3,4]
Output: [1,1,2,3,4,4]
Example 2:

Input: list1 = [], list2 = []
Output: []
Example 3:

Input: list1 = [], list2 = [0]
Output: [0]


Constraints:

The number of nodes in both lists is in the range [0, 50].
-100 <= Node.val <= 100
Both list1 and list2 are sorted in non-decreasing order.
"""
from typing import Optional


# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
class Solution:
    def mergeTwoLists(self, list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:
        if list1 is None:
            return list2
        elif list2 is None:
            return list1
        head1 = list1
        head2 = list2
        final_head = None
        cur_node = None
        while head1 is not None and head2 is not None:
            if head1.val <= head2.val:
                if cur_node is not None:
                    cur_node.next = head1
                else:
                    final_head = head1
                cur_node = head1
                head1 = head1.next
            else:
                if cur_node is not None:
                    cur_node.next = head2
                else:
                    final_head = head2
                cur_node = head2
                head2 = head2.next
        if head1 is not None:
            cur_node.next = head1
        elif head2 is not None:
            cur_node.next = head2
        return final_head