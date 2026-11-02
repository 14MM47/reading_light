"""Load KiCad symbols (flattening `extends`) and expose their pins in library coordinates."""
from __future__ import annotations

import copy
import os
from dataclasses import dataclass
from functools import lru_cache

from . import sexpr
from .sexpr import QStr

SYSTEM_SYM_DIR = "/usr/share/kicad/symbols"
EXTRA_LIBS: dict[str, str] = {}   # nickname -> path of a project .kicad_sym


@dataclass
class Pin:
    number: str
    name: str
    etype: str      # input, output, bidirectional, power_in, power_out, passive, no_connect, ...
    x: float        # library coords (mm, Y up) of the connection point
    y: float
    angle: int      # direction from connection point into the body (deg)
    length: float
    unit: int
    hidden: bool


@lru_cache(maxsize=None)
def _lib(nick: str):
    path = EXTRA_LIBS.get(nick) or os.path.join(SYSTEM_SYM_DIR, f"{nick}.kicad_sym")
    with open(path, encoding="utf-8") as f:
        tree = sexpr.parse(f.read())
    return {s[1]: s for s in sexpr.find_all(tree, "symbol")}


def load(lib_id: str):
    """Return a flattened symbol s-expression named `lib_id` (e.g. 'Device:R'), ready to embed."""
    nick, name = lib_id.split(":", 1)
    syms = _lib(nick)
    sym = copy.deepcopy(syms[name])
    ext = sexpr.find(sym, "extends")
    if ext is not None:
        parent = copy.deepcopy(load(f"{nick}:{ext[1]}"))
        pname = ext[1]
        # child keeps its own properties; graphics/pins come from the parent (renamed)
        child_props = {p[1]: p for p in sexpr.find_all(sym, "property")}
        flat = [parent[0], QStr(name)]
        for item in parent[2:]:
            if isinstance(item, list) and item and item[0] == "property" and item[1] in child_props:
                flat.append(child_props.pop(item[1]))
            elif isinstance(item, list) and item and item[0] == "symbol":
                sub = copy.deepcopy(item)
                pn = str(sub[1])
                full_parent = str(parent[1]).split(":")[-1]
                if pn.startswith(full_parent + "_"):
                    sub[1] = QStr(name + pn[len(full_parent):])
                flat.append(sub)
            else:
                flat.append(item)
        for p in child_props.values():
            flat.append(p)
        sym = flat
    sym[1] = QStr(lib_id)
    return sym


def pins(lib_id: str) -> list[Pin]:
    sym = load(lib_id)
    out: list[Pin] = []
    for sub in sexpr.find_all(sym, "symbol"):
        nm = str(sub[1])
        try:
            unit = int(nm.rsplit("_", 2)[-2])
        except (ValueError, IndexError):
            unit = 1
        for p in sexpr.find_all(sub, "pin"):
            at = sexpr.find(p, "at")
            length = float(sexpr.find(p, "length")[1])
            name = sexpr.find(p, "name")[1]
            number = sexpr.find(p, "number")[1]
            hidden = any(x == "hide" for x in p) or (sexpr.find(p, "hide") is not None and sexpr.find(p, "hide")[1] == "yes")
            out.append(Pin(str(number), str(name), str(p[1]), float(at[1]), float(at[2]),
                           int(float(at[3])) if len(at) > 3 else 0, length, unit, hidden))
    return out


def body_bbox(lib_id: str):
    """Approximate bbox (lib coords) from pins and rectangles."""
    xs, ys = [], []
    for p in pins(lib_id):
        xs.append(p.x)
        ys.append(p.y)
    sym = load(lib_id)
    for sub in sexpr.find_all(sym, "symbol"):
        for r in sexpr.find_all(sub, "rectangle"):
            s = sexpr.find(r, "start")
            e = sexpr.find(r, "end")
            xs += [float(s[1]), float(e[1])]
            ys += [float(s[2]), float(e[2])]
    if not xs:
        return (-2.54, -2.54, 2.54, 2.54)
    return (min(xs), min(ys), max(xs), max(ys))
