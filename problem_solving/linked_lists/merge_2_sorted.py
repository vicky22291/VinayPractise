"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/93/linked-list/771/
"""
from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def mergeTwoLists(self, list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:
        if not list1:
            return list2
        if not list2:
            return list1
        n1, n2 = list1, list2
        head = None
        prev = None
        while n1 and n2:
            if n1.val <= n2.val:
                if head is None:
                    head = n1
                else:
                    prev.next = n1
                prev = n1
                n1 = n1.next
            else:
                if head is None:
                    head = n2
                else:
                    prev.next = n2
                prev = n2
                n2 = n2.next
        if n1:
            prev.next = n1
        else:
            prev.next = n2
        return head