"""
    https://leetcode.com/explore/interview/card/top-interview-questions-hard/117/linked-list/840/
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
            return head
        node = head
        nodes = []
        while node:
            nodes.append(node)
            node = node.next
        nodes = sorted(nodes, key=lambda x: x.val)
        head = node = nodes[0]
        prev = None
        for node in nodes:
            if prev:
                prev.next = node
            prev = node
        prev.next = None
        return head