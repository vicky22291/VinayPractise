"""
    https://leetcode.com/explore/interview/card/top-interview-questions-easy/93/linked-list/773/
"""


class Solution(object):
    def hasCycle(self, head):
        """
        :type head: ListNode
        :rtype: bool
        """
        if head is None:
            return False
        slow_p = fast_p = head
        while slow_p:
            if not (fast_p.next and fast_p.next.next):
                return False
            slow_p = slow_p.next
            fast_p = fast_p.next.next
            if slow_p == fast_p:
                return True
        return False