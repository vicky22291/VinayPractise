"""
URL: https://www.hellointerview.com/learn/code/breadth-first-search/level-order-sum

DESCRIPTION
Given the root of a binary tree, return the sum of the nodes at each level. The output should be a list containing the sum of the nodes at each level.

Example 1:

Input:

[1, 3, 4, null, 2, 7, null, 8]
1
3
2
8
4
7
1
7
9
8
Output: [1, 7, 9, 8]

Example 2:

Input:

[1, 2, 5, 3, null, null, 4]
1
2
3
4
5
1
7
3
4
Output: [1, 7, 3, 4]
"""

class Solution:
    def level_order_sum(self, root: 'TreeNode'):
        if root is None:
            return []
        ans, q, nq = [0], [root], []
        while len(q):
            node = q.pop()
            ans[-1] += node.val
            if node.left:
                nq.append(node.left)
            if node.right:
                nq.append(node.right)
            if len(q) == 0 and len(nq) != 0:
                q, nq = nq, q
                ans.append(0)
        return ans