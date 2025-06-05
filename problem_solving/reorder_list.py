"""
URL: https://leetcode.com/problems/reorder-list/
"""
from collections import deque
from typing import Optional


# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
class Solution:
    def reorderList(self, head: Optional[ListNode]) -> None:
        """
        Do not return anything, modify head in-place instead.
        """
        if head.next is None or head.next.next is None:
            return head
        f, s, slow, fast = deque(), [], head, head
        while fast and fast.next:
            f.append(slow)
            if fast.next:
                fast = fast.next.next
            slow = slow.next
        if fast:
            f.append(slow)
            slow = slow.next
        while slow:
            s.append(slow)
            slow = slow.next
        last = None
        if fast:
            last = f.pop()
            last.next = None
        sp = None
        while len(f) and len(s):
            fn, sn = f.popleft(), s.pop()
            fn.next = sn
            if sp:
                sp.next = fn
            sp = sn
        sp.next = last
        return head