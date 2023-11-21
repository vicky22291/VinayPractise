"""
    https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/704/linked-lists/4597/
"""
from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def deleteDuplicates(self, head: Optional[ListNode]) -> Optional[ListNode]:
        if head is None:
            return head
        node = head
        prev = None
        while node:
            if prev:
                if prev.val != node.val:
                    prev.next = node
                    prev = node
            else:
                prev = node
            node = node.next
        prev.next = None
        return head