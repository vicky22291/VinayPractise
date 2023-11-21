"""
    https://leetcode.com/explore/interview/card/top-interview-questions-hard/116/array-and-strings/833/
"""


class Solution(object):
    def longestConsecutive(self, nums):
        """
        :type nums: List[int]
        :rtype: int
        """
        firsts = {}
        lasts = {}
        for i in nums:
            if i in firsts or i in lasts:
                pass
            elif i + 1 not in firsts and i - 1 not in lasts:
                new_array = [i]
                firsts[i] = new_array
                lasts[i] = new_array
            elif i + 1 in firsts:
                firsts[i + 1].insert(0, i)
                firsts[i] = firsts[i + 1]
                firsts.pop(i + 1)
                if i - 1 in lasts:
                    for val in firsts[i]:
                        lasts[i - 1].append(val)
                    lasts[lasts[i - 1][-1]] = lasts[i - 1]
                    firsts[lasts[i - 1][0]] = lasts[i - 1]
                    firsts.pop(i)
                    lasts.pop(i - 1)
            elif i - 1 in lasts:
                lasts[i - 1].append(i)
                lasts[i] = lasts[i - 1]
                lasts.pop(i - 1)
                if i + 1 in firsts:
                    for val in firsts[i]:
                        lasts[i].append(val)
                    lasts[lasts[i][-1]] = lasts[i]
                    firsts[lasts[i][0]] = lasts[i]
                    firsts.pop(i + 1)
                    lasts.pop(i)

        max_count = 0
        for first, values in firsts.items():
            max_count = max(max_count, len(values))

        return max_count