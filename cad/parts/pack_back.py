"""Pack back plate: closes the front shell, locates the LiPo pouch, carries the clip.

Requirements (newest last; never renumber):
  B1  GIVEN    (Matt) the pack encloses the battery
  B2  RULE     battery bay 36.0 x 64.5 mm with 0.6 mm swelling headroom over a 5.3 mm pouch (packlib)
  B3  ASSUMED  two bottom tabs hook into slots in the front shell's bottom wall; two M2 screws at the top go through
               the clip root and this plate into the front shell's bosses
  B4  RULE     printed outer face down (PETG); tab undersides slope 45 deg
  B5  RULE     (round2 R2-D2) everything on the plate stays inside the front shell's cavity (|X| <= IN_X - clear; above
               the bottom wall except the two tabs). The shell's side and bottom walls locate the pouch; only the
               top-end locators remain
"""
from __future__ import annotations

import sys
from pathlib import Path

from build123d import (Align, BuildPart, BuildSketch, Cylinder, Locations, Mode, Plane, Polygon, Pos, Rectangle,
                       RectangleRounded, extrude, Box)

sys.path.insert(0, str(Path(__file__).parent))
from _lib import packlib as K  # noqa: E402
from _lib.meshkit import claim  # noqa: E402

PRINT = {"material": "petg-basic", "process": "0.20-standard", "supports": "none", "supported": [],
         "orientation": "as-modelled"}
VERIFY = {"battery": "Pimoroni BAT0004 measured 64.0 x 35.5 x 5.3 mm (listing); measure the cell you receive"}
SCREWS = [(-13.0, K.IN_Y_TOP - 3.4), (13.0, K.IN_Y_TOP - 3.4)]
TABS_X = (-9.0, 9.0)


def part(*, clear=0.2):
    w = 2 * (K.IN_X - clear)
    y0, y1 = K.IN_Y_BOT + clear, K.IN_Y_TOP - clear
    bw, bl, _ = K.BAT
    bay_y0 = K.IN_Y_BOT + 0.5
    with BuildPart() as p:
        with BuildSketch(Plane.XY):
            with Locations((0, (y0 + y1) / 2)):
                RectangleRounded(w, y1 - y0, K.CORNER_R - K.WALL - clear)
        extrude(amount=K.BACK_T)
        # top-end battery locators, 2.0 mm tall, inside the cavity (the shell walls locate the sides and bottom end)
        x_in = K.IN_X - clear
        for sx in (-1, 1):
            with Locations((sx * (x_in - 3.2), bay_y0 + bl + 0.5, K.BACK_T)):
                Box(6.0, 1.0, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # screw clearance holes
        for (x, y) in SCREWS:
            with Locations((x, y, -0.1)):
                Cylinder(K.SCREW_CLEAR / 2, K.BACK_T + 0.3, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        # bottom tabs: 45 deg underside, top at Z 3.0, reaching 0.7 mm into the front shell's slots (Z 1.1-3.1)
        for x in TABS_X:
            with BuildSketch(Plane.YZ.offset(x - 3.0)):
                e = y0
                Polygon((e + 0.5, 1.2), (e, 1.2), (e - 0.9, 2.1), (e - 0.9, 3.0), (e + 0.5, 3.0), align=None)
            extrude(amount=6.0)
    return p.part


def context(p):
    bw, bl, bt = K.BAT
    bay_y0 = K.IN_Y_BOT + 0.5
    cell = Pos(0, bay_y0 + bl / 2, K.BACK_T) * Box(bw - 0.5, bl - 0.5, bt - 0.3, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return {"battery": cell}


def spec(m, p):
    lo, hi = m.bounds
    out = [claim("B2", "bay length fits a 64.5 mm pouch inside the cavity", K.IN_Y_BOT + 0.5 + K.BAT[1] < K.PCB_H / 2 + 5.0,
                 round(K.IN_Y_BOT + 0.5 + K.BAT[1], 2))]
    out.append(claim("B3", "screw holes open", all(not m.contains([[x, y, 0.9]])[0] for x, y in SCREWS)))
    out.append(claim("B4", "plate thickness", abs(K.BACK_T - 1.8) < 1e-6, K.BACK_T))
    out.append(claim("B5", "nothing beyond the shell's inner side walls", float(hi[0]) <= K.IN_X - 0.15 and
                     float(-lo[0]) <= K.IN_X - 0.15, round(float(max(hi[0], -lo[0])), 2)))
    probes = [[x, K.IN_Y_BOT - 0.05, K.BACK_T + 1.0] for x in (-17.0, -14.0, -2.0, 0.0, 2.0, 14.0, 17.0)]
    out.append(claim("B5", "nothing in the bottom wall above the plate except the tabs", not any(m.contains(probes))))
    return out
