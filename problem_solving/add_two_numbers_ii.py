"""
URL: https://leetcode.com/problems/add-two-numbers-ii/description
"""
from typing import Optional


# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        st1, st2 = [], []
        for head, st in [(l1, st1), (l2, st2)]:
            node = head
            while node:
                st.append(node)
                node = node.next
        if len(st1) < len(st2):
            st1, st2 = st2, st1
        cur = prev = None
        carry = 0
        while len(st1):
            n1 = st1.pop()
            n2 = st2.pop() if len(st2) else None
            s = n1.val + carry if n2 is None else n1.val + n2.val + carry
            if s >= 10:
                carry = 1
                cur = ListNode(s % 10, prev)
            else:
                carry = 0
                cur = ListNode(s, prev)
            prev = cur
        if carry:
            cur = ListNode(carry, prev)
        return cur