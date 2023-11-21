"""
    https://leetcode.com/problems/word-pattern/
"""
import unittest


class Solution:
    def wordPattern(self, pattern: str, s: str) -> bool:
        words = s.split(" ")
        if len(words) != len(pattern):
            return False
        data = {}
        wData = {}
        for index, char in enumerate(pattern):
            word = words[index]
            if char in data:
                if data[char] != word:
                    return False
            elif word in wData:
                return False
            else:
                data[char] = words[index]
                wData[words[index]] = char
            index += 1
        return True


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertTrue(sol.wordPattern("abba", "dog cat cat dog"))

    def testSample2(self):
        sol = Solution()
        self.assertFalse(sol.wordPattern("abba", "dog cat cat fish"))

    def testSample3(self):
        sol = Solution()
        self.assertFalse(sol.wordPattern("aaaa", "dog cat cat dog"))

    def testSample4(self):
        sol = Solution()
        self.assertFalse(sol.wordPattern("abba", "dog dog dog dog"))