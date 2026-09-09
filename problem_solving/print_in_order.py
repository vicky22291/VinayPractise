"""
URL: https://leetcode.com/problems/print-in-order/
"""


class Foo:
    def __init__(self):
        self.firstPrinted = False
        self.secondPrinted = False


    def first(self, printFirst: 'Callable[[], None]') -> None:
        # printFirst() outputs "first". Do not change or remove this line.
        printFirst()
        self.firstPrinted = True


    def second(self, printSecond: 'Callable[[], None]') -> None:
        while not self.firstPrinted:
            continue
        # printSecond() outputs "second". Do not change or remove this line.
        printSecond()
        self.secondPrinted = True


    def third(self, printThird: 'Callable[[], None]') -> None:
        while not self.secondPrinted:
            continue
        # printThird() outputs "third". Do not change or remove this line.
        printThird()