import collections
import unittest
from typing import List


"""
    https://leetcode.com/problems/synonymous-sentences/
"""


class Solution:
    def generateSentences(self, synonyms: List[List[str]], text: str) -> List[str]:
        finalData = collections.defaultdict(set)
        for key, value in synonyms:
            finalData[key] = finalData[value] = finalData[key].union(finalData[value])
            finalData[key].add(value)
            finalData[key].add(key)
            for word in finalData[key]:
                if word != key:
                    finalData[word] = finalData[key]
        sentence = text.split(' ')
        result = []

        def traverse(index, words, result):
            if index == len(words):
                result.append(words)
            else:
                traverse(index + 1, words, result)
                if words[index] in finalData:
                    for alternate in finalData[words[index]]:
                        if alternate != words[index]:
                            newWords = [word for word in words]
                            newWords[index] = alternate
                            traverse(index + 1, newWords, result)

        traverse(0, sentence, result)
        ans = [" ".join(words) for words in result]
        return sorted(ans)


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(["I am cheerful today but was sad yesterday", "I am cheerful today but was sorrow yesterday",
                          "I am happy today but was sad yesterday", "I am happy today but was sorrow yesterday",
                          "I am joy today but was sad yesterday", "I am joy today but was sorrow yesterday"],
                         sol.generateSentences([["happy", "joy"], ["sad", "sorrow"], ["joy", "cheerful"]],
                                               "I am happy today but was sad yesterday"))

    def testSample2(self):
        sol = Solution()
        self.assertEqual(
            ["a a", "a b", "a c", "a d", "a e", "b a", "b b", "b c", "b d", "b e", "c a", "c b", "c c", "c d", "c e",
             "d a", "d b", "d c", "d d", "d e", "e a", "e b", "e c", "e d", "e e"],
            sol.generateSentences([["a", "b"], ["b", "c"], ["d", "e"], ["c", "d"]], "a b"))
