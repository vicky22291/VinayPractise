"""Part 1 floor check. The interviewer grades REVIEW.md against answer-key.md §1.

This only proves the four blockers were found and the verdict is not approve.
"""
import os
import re
import unittest

GROUPS = {
    "retry can charge the card twice": r"idempot|double[- ]charg|charged? twice|duplicate charge|two charges",
    "float money loses cents": r"float|truncat|1998",
    "currencies without 2 decimals": r"jpy|krw|kwd|bhd|zero[- ]decimal|three[- ]decimal|exponent|minor unit",
    "swallowed error bills nothing": r"except|swallow|returns? 0|zero total|marks? (it )?paid|marked paid",
}
VERDICT = r"request(ed|ing)? changes|changes requested|do not merge|don't merge|not mergeable|block(s|ing)? (the )?merge"


def review_text():
    path = os.path.join(os.getcwd(), "REVIEW.md")
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return f.read().lower()


class Part1Review(unittest.TestCase):
    def setUp(self):
        self.text = review_text()
        if self.text is None:
            self.fail("REVIEW.md not found in the repo root")

    def test_uses_severities(self):
        self.assertIn("blocker", self.text)

    def test_finds_each_blocker(self):
        missing = [name for name, pat in GROUPS.items() if not re.search(pat, self.text)]
        self.assertEqual(missing, [], f"{len(missing)} of {len(GROUPS)} blockers not mentioned")

    def test_verdict_is_not_approve(self):
        self.assertRegex(self.text, VERDICT)


if __name__ == "__main__":
    unittest.main()
