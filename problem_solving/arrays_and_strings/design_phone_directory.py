"""
    https://leetcode.com/problems/design-phone-directory/
"""


class PhoneDirectory:

    def __init__(self, maxNumbers: int):
        self.directory = [-1] * maxNumbers
        self.maxNumbers = maxNumbers
        self.emptySlot = 0

    def get(self) -> int:
        while self.emptySlot < self.maxNumbers and self.directory[self.emptySlot] != -1:
            self.emptySlot += 1
        if self.emptySlot == self.maxNumbers:
            return -1
        else:
            self.directory[self.emptySlot] = 1
            ans = self.emptySlot
            self.emptySlot += 1
            return ans

    def check(self, number: int) -> bool:
        return self.directory[number] == -1

    def release(self, number: int) -> None:
        self.directory[number] = -1
        if self.emptySlot > number:
            self.emptySlot = number

# Your PhoneDirectory object will be instantiated and called as such:
# obj = PhoneDirectory(maxNumbers)
# param_1 = obj.get()
# param_2 = obj.check(number)
# obj.release(number)