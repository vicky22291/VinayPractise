"""
URL: https://leetcode.com/problems/minimum-penalty-for-a-shop/description
"""

class Solution:
    def bestClosingTime(self, customers: str) -> int:
        totalPenalty, n = 0, len(customers)
        for char in customers:
            if char == 'N':
                totalPenalty += 1
        minHour, minPenalty = n, totalPenalty
        for i in range(n - 1, -1, -1):
            if customers[i] == 'Y':
                totalPenalty += 1
            else:
                totalPenalty -= 1
            if minPenalty >= totalPenalty:
                minPenalty = totalPenalty
                minHour = i
        return minHour