"""
    https://leetcode.com/problems/double-a-number-represented-as-a-linked-list/description/
"""
# Definition for singly-linked list.
from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def doubleIt(self, head: Optional[ListNode]) -> Optional[ListNode]:
        def dfs(node):
            carry = 0
            if node.next:
                carry = dfs(node.next)
            total = node.val + node.val + carry
            node.val = total % 10
            return total // 10

        carry = dfs(head)
        if carry:
            return ListNode(val=carry, next=head)
        else:
            return head
