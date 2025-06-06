"""
URL: https://leetcode.com/problems/add-two-numbers/

You are given two non-empty linked lists representing two non-negative integers. The digits are stored in reverse order, and each of their nodes contains a single digit. Add the two numbers and return the sum as a linked list.

You may assume the two numbers do not contain any leading zero, except the number 0 itself.



Example 1:


Input: l1 = [2,4,3], l2 = [5,6,4]
Output: [7,0,8]
Explanation: 342 + 465 = 807.
Example 2:

Input: l1 = [0], l2 = [0]
Output: [0]
Example 3:

Input: l1 = [9,9,9,9,9,9,9], l2 = [9,9,9,9]
Output: [8,9,9,9,0,0,0,1]


Constraints:

The number of nodes in each linked list is in the range [1, 100].
0 <= Node.val <= 9
It is guaranteed that the list represents a number that does not have leading zeros.
"""
# Definition for singly-linked list.
from collections import deque
from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        s1, s2 = deque(), deque()
        for node, stack in zip([l1, l2], [s1, s2]):
            while node:
                stack.append(node.val)
                node = node.next
        carry = 0
        head = prev = None
        while len(s1) or len(s2):
            num1 = s1.popleft() if len(s1) else 0
            num2 = s2.popleft() if len(s2) else 0
            s = num1 + num2 + carry
            num, carry = s % 10, s // 10
            node = ListNode(val=num)
            if head is None:
                head = node
            if prev:
                prev.next = node
            prev = node
        if carry:
            node = ListNode(val=carry)
            if head is None:
                head = node
            if prev:
                prev.next = node
        return head