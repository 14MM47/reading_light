"""Generate simple rectangular IC symbols into a project .kicad_sym library."""
from __future__ import annotations

from . import sexpr
from .sexpr import QStr

P = 2.54


def _font(size=1.27):
    return ["effects", ["font", ["size", size, size]]]


def ic_symbol(name, ref, left, right, top=(), bottom=(), width=15.24, desc="", footprint="", datasheet="",
              keywords=""):
    """left/right/top/bottom: lists of (number, name, etype) or None (gap). Pins 2.54 mm long."""
    nl, nr = len(left), len(right)
    rows = max(nl, nr)
    h = (rows + 1) * P
    half_w = width / 2
    y_top = h / 2
    y_top = round(round(y_top / P) * P, 2)
    body = ["symbol", QStr(f"{name}_0_1"),
            ["rectangle", ["start", -half_w, y_top], ["end", half_w, y_top - (rows + 1) * P],
             ["stroke", ["width", 0.254], ["type", "default"]], ["fill", ["type", "background"]]]]
    pins = ["symbol", QStr(f"{name}_1_1")]

    def pin(num, pname, etype, x, y, ang, hide=False):
        node = ["pin", etype, "line", ["at", x, y, ang], ["length", P]]
        if hide:
            node.append(["hide", "yes"])
        node += [["name", QStr(pname), _font()], ["number", QStr(num), _font()]]
        pins.append(node)

    for i, p in enumerate(left):
        if p:
            pin(p[0], p[1], p[2], -half_w - P, y_top - (i + 1) * P, 0)
    for i, p in enumerate(right):
        if p:
            pin(p[0], p[1], p[2], half_w + P, y_top - (i + 1) * P, 180)
    for i, p in enumerate(top):
        if p:
            pin(p[0], p[1], p[2], (i - (len(top) - 1) / 2) * P, y_top + P, 270)
    yb = y_top - (rows + 1) * P
    for i, p in enumerate(bottom):
        if p:
            pin(p[0], p[1], p[2], (i - (len(bottom) - 1) / 2) * P, yb - P, 90)
    props = []
    for k, v, at, hide in (("Reference", ref, (-half_w, y_top + 1.27), False),
                           ("Value", name, (half_w, y_top + 1.27), False),
                           ("Footprint", footprint, (0, 0), True), ("Datasheet", datasheet, (0, 0), True),
                           ("Description", desc, (0, 0), True), ("ki_keywords", keywords, (0, 0), True)):
        eff = _font()
        if hide:
            eff.append(["hide", "yes"])
        props.append(["property", QStr(k), QStr(v), ["at", at[0], at[1], 0], eff])
    return ["symbol", QStr(name), ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"]] + props + [body, pins]


def write_lib(path, symbols):
    doc = ["kicad_symbol_lib", ["version", 20241209], ["generator", QStr("kigen")], ["generator_version", QStr("9.0")]]
    doc += symbols
    with open(path, "w", encoding="utf-8") as f:
        f.write(sexpr.dumps(doc) + "\n")
