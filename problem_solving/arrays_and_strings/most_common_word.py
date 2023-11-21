import collections
import unittest
from typing import List


class Solution:
    def mostCommonWord(self, paragraph: str, banned: List[str]) -> str:
        paragraph = paragraph.lower()
        for char in "!?',;.":
            paragraph = " ".join(paragraph.split(char))
        paragraph = " ".join(paragraph.split(" "))
        wordsInParagraph = []
        for word in paragraph.split(" "):
            if word:
                wordsInParagraph.append(word)
        wordCount = collections.Counter(wordsInParagraph)
        wordCount = sorted(wordCount.items(), key=lambda x: x[1], reverse=True)
        for word, count in wordCount:
            if word not in banned:
                return word
        return ""


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual("b", sol.mostCommonWord("a, a, a, a, b,b,b,c, c", ["a"]))