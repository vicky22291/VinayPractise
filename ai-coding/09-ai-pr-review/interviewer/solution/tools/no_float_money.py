"""Usage: python3 tools/no_float_money.py <dir>

Flags float money in Python code: float(...) calls, round(...) calls and float
literals. Prints path:line for each one. Exits 1 if it found any, 0 if clean.
"""
import ast
import os
import sys


def findings(path):
    with open(path) as f:
        tree = ast.parse(f.read(), filename=path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("float", "round"):
            yield node.lineno, f"{node.func.id}() call"
        elif isinstance(node, ast.Constant) and type(node.value) is float:
            yield node.lineno, f"float literal {node.value!r}"


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    found = 0
    for root, dirs, files in os.walk(argv[1]):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in sorted(files):
            if name.endswith(".py"):
                path = os.path.join(root, name)
                for line, what in sorted(findings(path)):
                    print(f"{path}:{line}: {what}")
                    found += 1
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
