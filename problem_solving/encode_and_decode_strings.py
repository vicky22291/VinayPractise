"""
URL: https://leetcode.com/problems/encode-and-decode-strings/

Design an algorithm to encode a list of strings to a string. The encoded string is then sent over the network and is decoded back to the original list of strings.

Machine 1 (sender) has the function:

string encode(vector<string> strs) {
  // ... your code
  return encoded_string;
}
Machine 2 (receiver) has the function:
vector<string> decode(string s) {
  //... your code
  return strs;
}
So Machine 1 does:

string encoded_string = encode(strs);
and Machine 2 does:

vector<string> strs2 = decode(encoded_string);
strs2 in Machine 2 should be the same as strs in Machine 1.

Implement the encode and decode methods.

You are not allowed to solve the problem using any serialize methods (such as eval).



Example 1:

Input: dummy_input = ["Hello","World"]
Output: ["Hello","World"]
Explanation:
Machine 1:
Codec encoder = new Codec();
String msg = encoder.encode(strs);
Machine 1 ---msg---> Machine 2

Machine 2:
Codec decoder = new Codec();
String[] strs = decoder.decode(msg);
Example 2:

Input: dummy_input = [""]
Output: [""]


Constraints:

1 <= strs.length <= 200
0 <= strs[i].length <= 200
strs[i] contains any possible characters out of 256 valid ASCII characters.


Follow up: Could you write a generalized algorithm to work on any possible set of characters?
"""
from typing import List


class Codec:
    def encode(self, strs: List[str]) -> str:
        """Encodes a list of strings to a single string.
        """
        encoded_string = ""
        for string in strs:
            encoded_string += f'[{len(string)}]{string}'
        return encoded_string

    def decode(self, s: str) -> List[str]:
        """Decodes a single string to a list of strings.
        """
        stack = []
        isOpen = stringReadInProgress = False
        numberOfChars = None
        charToBeRead = 0
        for char in s:
            if char == "[" and not isOpen and not stringReadInProgress:
                isOpen = True
                stack.append("")
                numberOfChars = ""
            elif isOpen and char in "1234567890":
                numberOfChars += char
            elif isOpen and char == ']':
                isOpen = False
                stringReadInProgress = True
                charToBeRead = int(numberOfChars)
                if charToBeRead == 0:
                    stringReadInProgress = False
                    numberOfChars = None
            elif stringReadInProgress and charToBeRead:
                stack[-1] += char
                charToBeRead -= 1
                if charToBeRead == 0:
                    numberOfChars = None
                    stringReadInProgress = False
        return stack


# Your Codec object will be instantiated and called as such:
# codec = Codec()
# codec.decode(codec.encode(strs))