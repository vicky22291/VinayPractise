"""Data types for radar-lite."""
import json
from dataclasses import dataclass

# A transaction is a plain dict: field name -> str | bool | int.
ACCEPT = "accept"
BLOCK = "block"
REVIEW = "review"
ACTIONS = {ACCEPT, BLOCK, REVIEW}
VERSIONS = {1, 2}  # 1: AND/OR left to right. 2: AND binds tighter than OR.


@dataclass(frozen=True)
class Rule:
    id: str
    action: str
    when: str
    version: int = 1

    def __post_init__(self):
        if self.action not in ACTIONS:
            raise ValueError(f"rule {self.id}: unknown action {self.action!r}")
        if self.version not in VERSIONS:
            raise ValueError(f"rule {self.id}: unknown version {self.version!r}")


@dataclass(frozen=True)
class Decision:
    action: str
    rule_id: str | None


def load_rules(path):
    with open(path) as f:
        return [Rule(**r) for r in json.load(f)]


def load_transaction(path):
    with open(path) as f:
        return json.load(f)
