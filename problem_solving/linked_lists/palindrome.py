"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/93/linked-list/772/
"""
from math import ceil
from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def isPalindrome(self, head: Optional[ListNode]) -> bool:
        if head is None or head.next is None:
            return True
        length, node = 0, head
        while node:
            length += 1
            node = node.next

        def checkBothDirections(current_node, iteration):
            response_node, is_equal = current_node, True
            if iteration != ceil(length / 2):
                response_node, is_equal = checkBothDirections(current_node.next, iteration + 1)
            elif length % 2 == 0:
                response_node = current_node.next
                is_equal = True
            if is_equal and response_node.val == current_node.val:
                return response_node.next, True
            else:
                return response_node.next, False

        node, is_equal = checkBothDirections(head, 1)
        return is_equal