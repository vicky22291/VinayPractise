"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/93/linked-list/560/
"""
from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        node, prev = head, None
        while node:
            node.next, node, prev = prev, node.next, node
        return prev