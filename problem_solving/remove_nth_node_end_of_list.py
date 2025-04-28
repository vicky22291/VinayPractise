"""
URL: https://leetcode.com/problems/remove-nth-node-from-end-of-list/description/

Given the head of a linked list, remove the nth node from the end of the list and return its head.



Example 1:


Input: head = [1,2,3,4,5], n = 2
Output: [1,2,3,5]
Example 2:

Input: head = [1], n = 1
Output: []
Example 3:

Input: head = [1,2], n = 1
Output: [1]


Constraints:

The number of nodes in the list is sz.
1 <= sz <= 30
0 <= Node.val <= 100
1 <= n <= sz


Follow up: Could you do this in one pass?
"""
# Definition for singly-linked list.
from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
class Solution:
    def removeNthFromEnd(self, head: Optional[ListNode], n: int) -> Optional[ListNode]:
        new_head = head

        def sub_remove(node: ListNode, parent: Optional[ListNode]):
            nonlocal new_head
            last_count = 0
            if node.next:
                last_count = sub_remove(node.next, node)
            last_count += 1
            if last_count == n:
                if parent:
                    parent.next = node.next
                else:
                    new_head = node.next
            return last_count

        sub_remove(head, None)
        return new_head
