import unittest
from typing import List


class Solution:
    def snakesAndLadders(self, board: List[List[int]]) -> int:
        n = len(board)
        lastNum = n * n

        def getCoordinates(num):
            nonlocal n, lastNum
            num -= 1
            x = n - 1 - (num // n)
            y = n - 1 - (num % n) if (num // n) % 2 else (num % n)
            return x, y

        curQ = [1]
        steps = 1
        seen = {1}
        nxtQ = []
        while curQ:
            num = curQ.pop()
            for i in range(num + 1, num + 7):
                x, y = getCoordinates(i)
                if i == lastNum:
                    return steps
                elif i > lastNum:
                    break
                elif (board[x][y] if board[x][y] != -1 else i) not in seen:
                    nxt = board[x][y] if board[x][y] != -1 else i
                    if nxt == lastNum:
                        return steps
                    nxtQ.append(nxt)
                    seen.add(nxt)
            if not curQ:
                nxtQ, curQ = curQ, nxtQ
                steps += 1
        return -1


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(4, sol.snakesAndLadders(
            [[-1, -1, -1, -1, -1, -1], [-1, -1, -1, -1, -1, -1], [-1, -1, -1, -1, -1, -1], [-1, 35, -1, -1, 13, -1],
             [-1, -1, -1, -1, -1, -1], [-1, 15, -1, -1, -1, -1]]))

    def testSample2(self):
        sol = Solution()
        self.assertEqual(1, sol.snakesAndLadders([[-1, -1], [-1, 3]]))

    def testSample3(self):
        sol = Solution()
        self.assertEqual(1, sol.snakesAndLadders([[-1, -1, -1], [-1, 9, 8], [-1, 8, 9]]))

    def testSample4(self):
        sol = Solution()
        self.assertEqual(2, sol.snakesAndLadders(
            [[-1, -1, 19, 10, -1], [2, -1, -1, 6, -1], [-1, 17, -1, 19, -1], [25, -1, 20, -1, -1],
             [-1, -1, -1, -1, 15]]))
