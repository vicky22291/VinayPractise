"""
    https://leetcode.com/problems/find-all-possible-recipes-from-given-supplies/
"""
import unittest
from typing import List


class Solution:
    def findAllRecipes(self, recipes: List[str], ingredients: List[List[str]], supplies: List[str]) -> List[str]:
        supplies = set(supplies)
        ans = []
        for index, recipe in enumerate(recipes):
            possible = True
            for ingredient in ingredients[index]:
                if ingredient not in supplies:
                    possible = False
                    break
            if possible:
                ans.append(recipe)
                supplies.add(recipe)
        return ans


class SolutionTest(unittest.TestCase):
    def testSample1(self):
        sol = Solution()
        self.assertEqual(["bread"], sol.findAllRecipes(["bread"], [["yeast", "flour"]], ["yeast", "flour", "corn"]))
