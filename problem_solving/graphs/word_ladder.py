import unittest
from collections import defaultdict, Counter
from datetime import datetime
from typing import List

"""
class Solution(object):
    def __init__(self):
        self.length = 0
        # Dictionary to hold combination of words that can be formed,
        # from any given word. By changing one letter at a time.
        self.all_combo_dict = defaultdict(list)

    def visitWordNode(self, queue, visited, others_visited):
        queue_size = len(queue)
        for _ in range(queue_size):
            current_word = queue.popleft()
            for i in range(self.length):
                # Intermediate words for current word
                intermediate_word = current_word[:i] + "*" + current_word[i + 1:]

                # Next states are all the words which share the same intermediate state.
                for word in self.all_combo_dict[intermediate_word]:
                    # If the intermediate state/word has already been visited from the
                    # other parallel traversal this means we have found the answer.
                    if word in others_visited:
                        return visited[current_word] + others_visited[word]
                    if word not in visited:
                        # Save the level as the value of the dictionary, to save number of hops.
                        visited[word] = visited[current_word] + 1
                        queue.append(word)

        return None

    def ladderLength(self, beginWord, endWord, wordList):
        if endWord not in wordList or not endWord or not beginWord or not wordList:
            return 0

        # Since all words are of same length.
        self.length = len(beginWord)

        for word in wordList:
            for i in range(self.length):
                # Key is the generic word
                # Value is a list of words which have the same intermediate generic word.
                self.all_combo_dict[word[:i] + "*" + word[i + 1:]].append(word)

        # Queues for birdirectional BFS
        queue_begin = collections.deque([beginWord])  # BFS starting from beginWord
        queue_end = collections.deque([endWord])  # BFS starting from endWord

        # Visited to make sure we don't repeat processing same word
        visited_begin = {beginWord: 1}
        visited_end = {endWord: 1}
        ans = None

        # We do a birdirectional search starting one pointer from begin
        # word and one pointer from end word. Hopping one by one.
        while queue_begin and queue_end:

            # Progress forward one step from the shorter queue
            if len(queue_begin) <= len(queue_end):
                ans = self.visitWordNode(queue_begin, visited_begin, visited_end)
            else:
                ans = self.visitWordNode(queue_end, visited_end, visited_begin)
            if ans:
                return ans

        return 0
"""

"""
    Problem: https://leetcode.com/explore/interview/card/leetcodes-interview-crash-course-data-structures-and-algorithms/707/traversals-trees-graphs/4637/
"""


class Solution:
    def ladderLength(self, beginWord: str, endWord: str, wordList: List[str]) -> int:
        if endWord not in wordList:
            return 0
        n = len(beginWord)

        def isNext(word1, word2):
            for index, char in enumerate(word1):
                if char != word2[index]:
                    if index < n - 1:
                        return word2[index + 1:] == word1[index + 1:]
                    else:
                        return True
            return False

        seen = {beginWord}
        curQ = [beginWord]
        nxtQ = []
        steps = 1
        while curQ:
            word = curQ.pop()
            for nxtWord in wordList:
                if nxtWord not in seen and isNext(word, nxtWord):
                    if nxtWord == endWord:
                        return steps + 1
                    seen.add(nxtWord)
                    nxtQ.append(nxtWord)
            if not curQ:
                curQ, nxtQ = nxtQ, curQ
                steps += 1
        return 0


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(6, sol.ladderLength("leet", "code", ["lest", "leet", "lose", "code", "lode", "robe", "lost"]))
