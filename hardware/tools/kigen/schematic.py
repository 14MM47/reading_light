"""Write a single-sheet KiCad 9 schematic: embedded symbols, a short wire stub on every pin,
a net label at the end of each stub, no-connect flags, PWR_FLAGs and text notes.

Each pin's net comes from the design description, so the drawing and the board are generated from
one source of truth. Symbol <-> footprint linkage uses deterministic UUIDs (uuid5 of project/ref).
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field

from . import sexpr, symlib
from .sexpr import QStr

GRID = 1.27


def uid(*parts) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "reading-light/" + "/".join(str(p) for p in parts)))


def snap(v: float) -> float:
    return round(round(v / GRID) * GRID, 4)


@dataclass
class Part:
    ref: str
    lib_id: str
    value: str
    footprint: str
    pins: dict            # pin number -> net name, or None for an intentional no-connect
    sch: tuple = (0, 0, 0)      # schematic x, y (mm), rotation
    fields: dict = field(default_factory=dict)   # extra properties: MPN, Manufacturer, Farnell, Datasheet...
    in_bom: bool = True
    on_board: bool = True
    dnp: bool = False


def _rot(x, y, r):
    c, s = math.cos(math.radians(r)), math.sin(math.radians(r))
    return x * c - y * s, x * s + y * c


def _prop(name, value, at, hide=False, size=1.27, justify=None, angle=0):
    eff = ["effects", ["font", ["size", size, size]]]
    if justify:
        eff.append(["justify", justify])
    if hide:
        eff.append(["hide", "yes"])
    return ["property", QStr(name), QStr(value), ["at", at[0], at[1], angle], eff]


class Schematic:
    def __init__(self, project: str, title: str, rev: str, date: str, paper: str = "A3", company: str = ""):
        self.project, self.title, self.rev, self.date, self.paper, self.company = project, title, rev, date, paper, company
        self.root = uid(project, "root")
        self.items: list = []
        self.libs: dict[str, list] = {}
        self.parts: list[Part] = []
        self.pin_points: dict = {}   # (ref, pin) -> (x, y) of the stub end
        self.n_flags = 0
        self.comments: list[str] = []

    # ---------------------------------------------------------------- symbols
    def _embed(self, lib_id):
        if lib_id not in self.libs:
            self.libs[lib_id] = symlib.load(lib_id)

    def add(self, p: Part, stub: float = 2.54):
        self._embed(p.lib_id)
        self.parts.append(p)
        X, Y, R = p.sch
        X, Y = snap(X), snap(Y)
        sym_pins = symlib.pins(p.lib_id)
        numbers = {sp.number for sp in sym_pins}
        missing = numbers - set(p.pins)
        extra = set(p.pins) - numbers
        if missing or extra:
            raise ValueError(f"{p.ref} ({p.lib_id}): unmapped pins {sorted(missing)}; unknown pins {sorted(extra)}")
        props = [
            _prop("Reference", p.ref, (X, Y - 1.27)),
            _prop("Value", p.value, (X, Y + 1.27)),
            _prop("Footprint", p.footprint, (X, Y), hide=True),
            _prop("Datasheet", p.fields.get("Datasheet", ""), (X, Y), hide=True),
            _prop("Description", p.fields.get("Description", ""), (X, Y), hide=True),
        ]
        for k, v in p.fields.items():
            if k in ("Datasheet", "Description"):
                continue
            props.append(_prop(k, str(v), (X, Y), hide=True))
        # place Reference/Value outside the body bbox
        bx0, by0, bx1, by1 = symlib.body_bbox(p.lib_id)
        corners = [_rot(x, y, R) for x in (bx0, bx1) for y in (by0, by1)]
        sx0 = min(c[0] for c in corners); sx1 = max(c[0] for c in corners)
        sy0 = -max(c[1] for c in corners); sy1 = -min(c[1] for c in corners)
        props[0][3] = ["at", round(X + sx1 + 1.0, 3), round(Y + sy0 - 0.5, 3), 0]
        props[0][4].append(["justify", "left"])
        props[1][3] = ["at", round(X + sx1 + 1.0, 3), round(Y + sy0 + 1.6, 3), 0]
        props[1][4].append(["justify", "left"])
        node = ["symbol", ["lib_id", QStr(p.lib_id)], ["at", X, Y, R], ["unit", 1],
                ["exclude_from_sim", "no"], ["in_bom", "yes" if p.in_bom else "no"],
                ["on_board", "yes" if p.on_board else "no"], ["dnp", "yes" if p.dnp else "no"],
                ["uuid", QStr(uid(self.project, "sym", p.ref))]] + props
        seen = set()
        for sp in sym_pins:
            if sp.number in seen:
                continue
            seen.add(sp.number)
            node.append(["pin", QStr(sp.number), ["uuid", QStr(uid(self.project, "pin", p.ref, sp.number))]])
        node.append(["instances", ["project", QStr(self.project),
                                   ["path", QStr("/" + self.root), ["reference", QStr(p.ref)], ["unit", 1]]]])
        self.items.append(node)
        # stubs + labels (one per distinct connection point)
        done = {}
        for sp in sym_pins:
            px, py = _rot(sp.x, sp.y, R)
            ax, ay = X + px, Y - py
            key = (round(ax, 3), round(ay, 3))
            net = p.pins[sp.number]
            if key in done:
                if done[key] != net:
                    raise ValueError(f"{p.ref}: stacked pins at {key} on different nets {done[key]} / {net}")
                continue
            done[key] = net
            dx, dy = _rot(math.cos(math.radians(sp.angle + 180)), math.sin(math.radians(sp.angle + 180)), R)
            dx, dy = round(dx), round(-dy)
            if net is None:
                self.items.append(["no_connect", ["at", round(ax, 3), round(ay, 3)],
                                   ["uuid", QStr(uid(self.project, "nc", p.ref, sp.number))]])
                continue
            ex, ey = round(ax + dx * stub, 3), round(ay + dy * stub, 3)
            self.items.append(["wire", ["pts", ["xy", round(ax, 3), round(ay, 3)], ["xy", ex, ey]],
                               ["stroke", ["width", 0], ["type", "default"]],
                               ["uuid", QStr(uid(self.project, "w", p.ref, sp.number))]])
            ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[(dx, dy)]
            just = "left" if ang in (0, 90) else "right"
            self.items.append(["label", QStr(net), ["at", ex, ey, ang],
                               ["effects", ["font", ["size", 1.0, 1.0]], ["justify", just, "bottom"]],
                               ["uuid", QStr(uid(self.project, "lbl", p.ref, sp.number))]])
            self.pin_points[(p.ref, sp.number)] = (ex, ey)

    def pwr_flag(self, net: str, at):
        """PWR_FLAG on a net (tells ERC the net is driven by a connector/switch)."""
        self.n_flags += 1
        ref = f"#FLG{self.n_flags:02d}"
        part = Part(ref, "power:PWR_FLAG", "PWR_FLAG", "", {"1": net}, sch=(at[0], at[1], 0), in_bom=False, on_board=False)
        self.add(part, stub=2.54)
        self.parts.remove(part)

    def text(self, s: str, at, size: float = 1.5, bold: bool = False):
        font = ["font", ["size", size, size]]
        if bold:
            font.append(["bold", "yes"])
        self.items.append(["text", QStr(s), ["exclude_from_sim", "no"], ["at", at[0], at[1], 0],
                           ["effects", font, ["justify", "left", "bottom"]],
                           ["uuid", QStr(uid(self.project, "txt", s[:40], at))]])

    def box(self, x0, y0, x1, y1, label=None):
        self.items.append(["rectangle", ["start", x0, y0], ["end", x1, y1],
                           ["stroke", ["width", 0.15], ["type", "dash"]], ["fill", ["type", "none"]],
                           ["uuid", QStr(uid(self.project, "box", x0, y0))]])
        if label:
            self.text(label, (x0 + 1.0, y0 + 3.0), size=2.0, bold=True)

    # ---------------------------------------------------------------- output
    def write(self, path: str):
        tb = ["title_block", ["title", QStr(self.title)], ["date", QStr(self.date)], ["rev", QStr(self.rev)],
              ["company", QStr(self.company)]]
        for i, c in enumerate(self.comments[:9], 1):
            tb.append(["comment", i, QStr(c)])
        doc = ["kicad_sch", ["version", 20250114], ["generator", QStr("eeschema")], ["generator_version", QStr("9.0")],
               ["uuid", QStr(self.root)], ["paper", QStr(self.paper)], tb,
               ["lib_symbols"] + list(self.libs.values())]
        doc += self.items
        doc += [["sheet_instances", ["path", QStr("/"), ["page", QStr("1")]]], ["embedded_fonts", "no"]]
        with open(path, "w", encoding="utf-8") as f:
            f.write(sexpr.dumps(doc) + "\n")

    def netlist(self):
        """{net: [(ref, pin), ...]} from the design description (for the board builder and checks)."""
        nets: dict[str, list] = {}
        for p in self.parts:
            for num, net in p.pins.items():
                if net is not None:
                    nets.setdefault(net, []).append((p.ref, num))
        return nets
