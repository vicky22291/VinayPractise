"""
https://leetcode.com/problems/convert-binary-number-in-a-linked-list-to-integer/
"""

# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def getDecimalValue(self, head: Optional[ListNode]) -> int:
        result = 0
        while head:
            result = result*2 + head.val
            head = head.next
        return result