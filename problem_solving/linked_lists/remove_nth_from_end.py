"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/93/linked-list/603/
"""
from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def removeNthFromEnd(self, head: Optional[ListNode], n: int) -> Optional[ListNode]:
        def delete(node, k, parent):
            if node.next is None:
                if k == 1 and parent:
                    parent.next = None
                return 1
            fromEnd = delete(node.next, k, node) + 1
            if k == fromEnd:
                if parent:
                    parent.next = node.next
            return fromEnd
        fromEnd = delete(head, n, None)
        if fromEnd == n:
            return head.next
        else:
            return head