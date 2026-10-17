"""Find the files partner banks dropped for us.

Banks upload to one folder with names like `firstbank-20261016.csv`. Each bank
sends at most one file a day. We validate the newest file per bank.
"""
import os
import re
from dataclasses import dataclass

NAME = re.compile(r"^(?P<bank>[a-z0-9]+)-(?P<day>\d{8})\.csv$")


@dataclass(frozen=True)
class DropFile:
    bank: str
    day: str  # YYYYMMDD
    path: str


def list_drops(folder):
    """Every well-named CSV in the folder. Other files are ignored."""
    drops = []
    for name in sorted(os.listdir(folder)):
        m = NAME.match(name)
        if m:
            drops.append(DropFile(m["bank"], m["day"], os.path.join(folder, name)))
    return drops


def latest_per_bank(drops):
    """The newest drop for each bank, sorted by bank name."""
    newest = {}
    for d in drops:
        if d.bank not in newest or d.day > newest[d.bank].day:
            newest[d.bank] = d
    return [newest[b] for b in sorted(newest)]
