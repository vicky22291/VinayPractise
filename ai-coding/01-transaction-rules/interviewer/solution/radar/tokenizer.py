"""Split a `when` clause into tokens. Quoted text is never split or keyword-matched."""
import re
from dataclasses import dataclass

from radar.errors import RuleSyntaxError

_TOKEN = re.compile(
    r"""
    (?P<ws>\s+)
  | (?P<string>"[^"]*")
  | (?P<number>-?\d+)
  | (?P<op>==|!=|>=|<=|>|<)
  | (?P<lparen>\()
  | (?P<rparen>\))
  | (?P<word>[A-Za-z_][A-Za-z0-9_]*)
    """,
    re.VERBOSE,
)


@dataclass(frozen=True)
class Token:
    kind: str  # string number bool field op and or lparen rparen
    value: object
    pos: int


def tokenize(text):
    tokens, pos = [], 0
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m:
            what = "unterminated string" if text[pos] == '"' else f"unexpected {text[pos]!r}"
            raise RuleSyntaxError(f"{what} at column {pos}")
        kind, raw = m.lastgroup, m.group()
        if kind == "string":
            tokens.append(Token("string", raw[1:-1], pos))
        elif kind == "number":
            tokens.append(Token("number", int(raw), pos))
        elif kind == "word":
            low = raw.lower()
            if low in ("and", "or"):
                tokens.append(Token(low, low.upper(), pos))
            elif raw in ("true", "false"):
                tokens.append(Token("bool", raw == "true", pos))
            else:
                tokens.append(Token("field", raw, pos))
        elif kind != "ws":
            tokens.append(Token(kind, raw, pos))
        pos = m.end()
    return tokens
