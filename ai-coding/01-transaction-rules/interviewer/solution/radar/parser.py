"""Parse a `when` clause into a small tree, evaluate it, and print it back.

Grammar (version 1, left to right):   expr := primary (("AND" | "OR") primary)*
Grammar (version 2, AND before OR):   expr := term ("OR" term)*   term := primary ("AND" primary)*
Both:   primary := "(" expr ")" | operand OP operand
        operand := field | string | number | true | false
"""
import functools
import operator
from dataclasses import dataclass

from radar.errors import RuleSyntaxError
from radar.tokenizer import tokenize

MISSING = object()
_ORDERING = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le}


@dataclass(frozen=True)
class Field:
    name: str

    def value(self, txn):
        return txn.get(self.name, MISSING)

    def render(self):
        return self.name


@dataclass(frozen=True)
class Literal:
    val: object

    def value(self, txn):
        return self.val

    def render(self):
        if isinstance(self.val, bool):
            return "true" if self.val else "false"
        if isinstance(self.val, int):
            return str(self.val)
        return f'"{self.val}"'


@dataclass(frozen=True)
class Compare:
    op: str
    left: object
    right: object

    def eval(self, txn):
        a, b = self.left.value(txn), self.right.value(txn)
        if a is MISSING or b is MISSING or type(a) is not type(b):
            return False  # type() not isinstance(): True must never equal 1
        if self.op == "==":
            return a == b
        if self.op == "!=":
            return a != b
        return type(a) is int and _ORDERING[self.op](a, b)

    def render(self):
        return f"{self.left.render()} {self.op} {self.right.render()}"


@dataclass(frozen=True)
class BoolOp:
    op: str  # AND or OR
    left: object
    right: object

    def eval(self, txn):
        if self.op == "AND":
            return self.left.eval(txn) and self.right.eval(txn)
        return self.left.eval(txn) or self.right.eval(txn)

    def render(self):
        # Fully parenthesised, so it means the same under either version.
        return f"({self.left.render()} {self.op} {self.right.render()})"


class _Parser:
    def __init__(self, text, version):
        self.toks = tokenize(text)
        self.i = 0
        self.version = version

    def peek(self):
        return self.toks[self.i].kind if self.i < len(self.toks) else None

    def take(self, *kinds):
        if self.peek() not in kinds:
            got = "end of rule" if self.peek() is None else repr(self.toks[self.i].value)
            raise RuleSyntaxError(f"expected {' or '.join(kinds)}, got {got}")
        self.i += 1
        return self.toks[self.i - 1]

    def parse(self):
        tree = self.expr()
        if self.peek() is not None:
            raise RuleSyntaxError(f"unexpected {self.toks[self.i].value!r} at column {self.toks[self.i].pos}")
        return tree

    def expr(self):
        if self.version == 1:
            return self.chain(self.primary, ("and", "or"))
        return self.chain(self.term, ("or",))

    def term(self):
        return self.chain(self.primary, ("and",))

    def chain(self, sub, ops):
        left = sub()
        while self.peek() in ops:
            op = self.take(*ops).value
            left = BoolOp(op, left, sub())
        return left

    def primary(self):
        if self.peek() == "lparen":
            self.take("lparen")
            inner = self.expr()
            self.take("rparen")
            return inner
        left = self.operand()
        op = self.take("op").value
        return Compare(op, left, self.operand())

    def operand(self):
        tok = self.take("field", "string", "number", "bool")
        return Field(tok.value) if tok.kind == "field" else Literal(tok.value)


@functools.lru_cache(maxsize=10_000)
def parse(text, version=1):
    return _Parser(text, version).parse()
