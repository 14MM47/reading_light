"""Minimal S-expression reader/writer that round-trips KiCad files.

Atoms are kept as Python str. Quoted strings are wrapped in QStr so they are written back quoted.
Lists are Python lists. Numbers stay as their original text (str) so nothing is reformatted.
"""
from __future__ import annotations


class QStr(str):
    """A string that was (or must be) written in double quotes."""


def parse(text: str):
    pos = 0
    n = len(text)
    stack: list[list] = []
    root: list = []
    cur = root
    while pos < n:
        c = text[pos]
        if c in " \t\r\n":
            pos += 1
        elif c == "(":
            new: list = []
            cur.append(new)
            stack.append(cur)
            cur = new
            pos += 1
        elif c == ")":
            cur = stack.pop()
            pos += 1
        elif c == '"':
            pos += 1
            buf = []
            while True:
                ch = text[pos]
                if ch == "\\":
                    nxt = text[pos + 1]
                    buf.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, "\\" + nxt))
                    pos += 2
                elif ch == '"':
                    pos += 1
                    break
                else:
                    buf.append(ch)
                    pos += 1
            cur.append(QStr("".join(buf)))
        else:
            start = pos
            while pos < n and text[pos] not in ' \t\r\n()"':
                pos += 1
            cur.append(text[start:pos])
    if stack:
        raise ValueError("unbalanced parentheses")
    return root[0] if len(root) == 1 else root


def _atom(a) -> str:
    if isinstance(a, QStr):
        return '"' + a.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    if isinstance(a, bool):
        return "yes" if a else "no"
    if isinstance(a, float):
        s = f"{a:.4f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    return str(a)


def dumps(node, indent: int = 0) -> str:
    if not isinstance(node, list):
        return _atom(node)
    # short lists of atoms on one line
    if all(not isinstance(x, list) for x in node) and len(node) <= 8:
        return "(" + " ".join(_atom(x) for x in node) + ")"
    tab = "\t" * (indent + 1)
    parts = []
    head = []
    i = 0
    while i < len(node) and not isinstance(node[i], list):
        head.append(_atom(node[i]))
        i += 1
    out = "(" + " ".join(head)
    for x in node[i:]:
        if isinstance(x, list):
            parts.append("\n" + tab + dumps(x, indent + 1))
        else:
            parts.append(" " + _atom(x))
    return out + "".join(parts) + "\n" + "\t" * indent + ")"


def find(node, key):
    """First direct child list whose head is key."""
    for x in node:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None


def find_all(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]
