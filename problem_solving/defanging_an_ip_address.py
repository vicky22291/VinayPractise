"""
URL: https://leetcode.com/problems/defanging-an-ip-address/description
"""


class Solution:
    def defangIPaddr(self, address: str) -> str:
        return "[.]".join(address.split("."))