"""
    https://leetcode.com/explore/interview/card/top-interview-questions-hard/117/linked-list/839/
    We can also use heapq.heapify or heappush and heappop with a custom node where __lt__ is overridden.
"""
# Definition for singly-linked list.
# class ListNode(object):
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next


class Solution(object):
    def __init__(self):
        self.heap = []

    @staticmethod
    def __getParent(pos):
        return pos // 2 - (0 if pos % 2 else 1)

    @staticmethod
    def __leftChild(pos):
        return 2 * pos + 1

    @staticmethod
    def __rightChild(pos):
        return 2 * pos + 2

    def __isLeaf(self, pos):
        return len(self.heap) < (2 * (pos + 1))

    def __insert(self, node):
        self.heap.append(node)
        current_pos = len(self.heap) - 1
        parent = Solution.__getParent(current_pos)
        while parent >= 0 and self.heap[parent].val > self.heap[current_pos].val:
            self.heap[parent], self.heap[current_pos] = self.heap[current_pos], self.heap[parent]
            current_pos = parent
            parent = Solution.__getParent(current_pos)

    def __heapify(self, pos):
        if not self.__isLeaf(pos):
            leftChild = Solution.__leftChild(pos)
            rightChild = Solution.__rightChild(pos)
            if (leftChild < len(self.heap) and self.heap[pos].val > self.heap[leftChild].val) or \
                    (rightChild < len(self.heap) and self.heap[pos].val > self.heap[rightChild].val):
                if rightChild < len(self.heap) and self.heap[rightChild].val < self.heap[leftChild].val:
                    self.heap[pos], self.heap[rightChild] = self.heap[rightChild], self.heap[pos]
                    self.__heapify(rightChild)
                else:
                    self.heap[pos], self.heap[leftChild] = self.heap[leftChild], self.heap[pos]
                    self.__heapify(leftChild)

    def __removeTop(self):
        self.heap[0], self.heap[-1] = self.heap[-1], self.heap[0]
        top_node = self.heap.pop()
        self.__heapify(0)
        return top_node

    def mergeKLists(self, lists):
        """
        :type lists: List[ListNode]
        :rtype: ListNode
        """
        for i in lists:
            if i is not None:
                self.__insert(i)
        new_head = None
        last_node = None
        while len(self.heap):
            top_node = self.__removeTop()
            if new_head is None:
                new_head = top_node
            if top_node.next:
                self.__insert(top_node.next)
            if last_node:
                last_node.next = top_node
            last_node = top_node
        return new_head
