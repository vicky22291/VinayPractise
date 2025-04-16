"""
URL: https://leetcode.com/problems/palindrome-linked-list/description/

Given the head of a singly linked list, return true if it is a palindrome or false otherwise.



Example 1:


Input: head = [1,2,2,1]
Output: true
Example 2:


Input: head = [1,2]
Output: false


Constraints:

The number of nodes in the list is in the range [1, 105].
0 <= Node.val <= 9


Follow up: Could you do it in O(n) time and O(1) space?
"""
from typing import Optional


# Definition for singly-linked list.
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
class Solution:
    def isPalindrome(self, head: Optional[ListNode]) -> bool:
        def sub_isPalindrome(node: ListNode, front_node: ListNode):
            is_palindrome = True
            new_front_node = front_node
            if node.next:
                is_palindrome, new_front_node = sub_isPalindrome(node.next, front_node)
            if is_palindrome and node.val == new_front_node.val:
                return True, new_front_node.next
            return False, new_front_node.next
        is_palindrome, _ = sub_isPalindrome(head, head)
        return is_palindrome