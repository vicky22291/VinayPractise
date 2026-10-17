"""Data types for radar-lite."""
import json
from dataclasses import dataclass

# A transaction is a plain dict: field name -> str | bool | int.
ACCEPT = "accept"
BLOCK = "block"
ACTIONS = {ACCEPT, BLOCK}


@dataclass(frozen=True)
class Rule:
    id: str
    action: str
    when: str

    def __post_init__(self):
        if self.action not in ACTIONS:
            raise ValueError(f"rule {self.id}: unknown action {self.action!r}")


def load_rules(path):
    with open(path) as f:
        return [Rule(**r) for r in json.load(f)]


def load_transaction(path):
    with open(path) as f:
        return json.load(f)
