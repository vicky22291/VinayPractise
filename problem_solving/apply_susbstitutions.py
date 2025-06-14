"""
URL: https://leetcode.com/problems/apply-substitutions/description
"""
from typing import List


class Solution:
    def applySubstitutions(self, replacements: List[List[str]], text: str) -> str:
        rep = {key: value for key, value in replacements}
        while '%' in text:
            splits = text.split("%")
            for i, word in enumerate(splits):
                if word in rep:
                    splits[i] = rep[word]
            text = "".join(splits)
        return text