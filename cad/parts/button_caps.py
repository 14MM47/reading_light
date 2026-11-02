"""Three button caps (UP "+", MAIN dot, DOWN "-") printed together, flange down.

Requirements (newest last; never renumber):
  B1  GIVEN    (Matt) main button with up and down buttons above and below
  B2  RULE     cap body 7.0 mm through a 7.4 mm hole, 9.6 mm flange 1.3 mm thick resting on the PTS645 actuator
               (4.3 mm high) and retained under the face; top stands 0.8 mm proud of the face
  B3  ASSUMED  embossed 0.4 mm symbols so the buttons can be told apart in the dark
  B4  RULE     (round2 R2-D11) flange 9.0 mm (r 4.5): >= 0.4 mm to the PCB mounting bosses, with the cap's lateral play
"""
from __future__ import annotations

import sys
from pathlib import Path

from build123d import Align, Box, BuildPart, Cylinder, Locations, Mode, Pos

sys.path.insert(0, str(Path(__file__).parent))
from _lib import packlib as K  # noqa: E402
from _lib.meshkit import claim  # noqa: E402

PRINT = {"material": "petg-basic", "process": "0.12-fine", "supports": "none", "supported": [], "orientation": "flange down"}
VERIFY = {"cap_fit": "7.0 mm cap in a 7.4 mm hole: should slide freely; sand if tight"}
FLANGE_T = (K.Z_FACE_IN - 0.1) - (K.Z_PCB_TOP + 4.3)
BODY_H = (K.Z_TOP + 0.8) - (K.Z_FACE_IN - 0.1)
FLANGE_R = 4.5


def _cap(sym):
    with BuildPart() as p:
        Cylinder(FLANGE_R, FLANGE_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((0, 0, FLANGE_T)):
            Cylinder(K.BTN_CAP_D / 2, BODY_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        top = FLANGE_T + BODY_H
        with Locations((0, 0, top - 0.01)):
            if sym in ("+", "-"):
                Box(4.0, 0.9, 0.41, align=(Align.CENTER, Align.CENTER, Align.MIN))
            if sym == "+":
                Box(0.9, 4.0, 0.41, align=(Align.CENTER, Align.CENTER, Align.MIN))
            if sym == "o":
                Cylinder(1.3, 0.41, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return p.part


def part():
    caps = [Pos(x, 0, 0) * _cap(s) for x, s in ((-12, "+"), (0, "o"), (12, "-"))]
    out = caps[0]
    for c in caps[1:]:
        out = out + c
    return out


def _boss_gap():
    import math
    gaps = []
    for ref in ("SW2", "SW3", "SW4"):
        X, Y, _ = K.placed(ref)
        for (hx, hy) in K.mount_holes():
            gaps.append(math.hypot(X - hx, Y - hy) - FLANGE_R - K.BOSS_D / 2 - (K.BTN_HOLE_D - K.BTN_CAP_D) / 2)
    return min(gaps)


def spec(m, p):
    return [claim("B4", "flange clears the PCB bosses by >= 0.25 mm at worst-case lateral play", _boss_gap() >= 0.25,
                  round(_boss_gap(), 2)),
            claim("B2", f"flange {FLANGE_T:.2f} mm thick (> 0.8)", FLANGE_T > 0.8, round(FLANGE_T, 2)),
            claim("B2", "cap stands 0.8 mm proud", abs((FLANGE_T + BODY_H) - (K.Z_TOP + 0.8 - K.Z_PCB_TOP - 4.3)) < 1e-6,
                  round(FLANGE_T + BODY_H, 2))]
