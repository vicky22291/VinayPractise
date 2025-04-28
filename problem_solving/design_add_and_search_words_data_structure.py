"""
URL: https://leetcode.com/problems/design-add-and-search-words-data-structure/

Design a data structure that supports adding new words and finding if a string matches any previously added string.

Implement the WordDictionary class:

WordDictionary() Initializes the object.
void addWord(word) Adds word to the data structure, it can be matched later.
bool search(word) Returns true if there is any string in the data structure that matches word or false otherwise. word may contain dots '.' where dots can be matched with any letter.


Example:

Input
["WordDictionary","addWord","addWord","addWord","search","search","search","search"]
[[],["bad"],["dad"],["mad"],["pad"],["bad"],[".ad"],["b.."]]
Output
[null,null,null,null,false,true,true,true]

Explanation
WordDictionary wordDictionary = new WordDictionary();
wordDictionary.addWord("bad");
wordDictionary.addWord("dad");
wordDictionary.addWord("mad");
wordDictionary.search("pad"); // return False
wordDictionary.search("bad"); // return True
wordDictionary.search(".ad"); // return True
wordDictionary.search("b.."); // return True


Constraints:

1 <= word.length <= 25
word in addWord consists of lowercase English letters.
word in search consist of '.' or lowercase English letters.
There will be at most 2 dots in word for search queries.
At most 104 calls will be made to addWord and search.
"""

class Node:
    def __init__(self, val: str, isEnd: bool = False):
        self.val = val
        self.isEnd = isEnd
        self.next = {}

class WordDictionary:

    def __init__(self):
        self.root = Node("")

    def addWord(self, word: str) -> None:
        cur = self.root
        for char in word:
            if char not in cur.next:
                cur.next[char] = Node(char)
            cur = cur.next[char]
        cur.isEnd = True

    def search(self, word: str) -> bool:
        def dfs(node: Node, string: str) -> bool:
            n, cur = len(string), node
            if n and len(cur.next) == 0:
                return False
            for i, char in enumerate(string):
                if char == ".":
                    ## If last character
                    if i == n - 1:
                        return any([next_node.isEnd for next_char, next_node in cur.next.items()])
                    else:
                        return any([dfs(next_node, string[i + 1:]) for existing_char, next_node in cur.next.items()])
                elif char in cur.next:
                    cur = cur.next[char]
                else:
                    return False
            return cur.isEnd
        return dfs(self.root, word)


actions = ["WordDictionary","addWord","addWord","search","search","search","search","search","search"]
inputs = [[],["a"],["a"],["."],["a"],["aa"],["a"],[".a"],["a."]]
dictionary = None
for i, input in enumerate(inputs):
    action = actions[i]
    if action == "WordDictionary":
        dictionary = WordDictionary()
    elif action == "addWord":
        dictionary.addWord(input[0])
    elif action == "search":
        print(dictionary.search(input[0]))