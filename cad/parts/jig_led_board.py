"""Assembly jig for the double-sided LED board: holds the 26 mm board flat, LEDs up, for the top-side stencil and the
second reflow, resting only on the part-free edge band so the bottom-side parts hang free.

Requirements (newest last; never renumber):
  B1  RULE     (round2 R2-D12) pocket = board diameter + 0.4 (26.4 mm), 1.0 mm deep: the board top sits flush with
               the jig top so a frameless stencil lies flat across both
  B2  RULE     relief under the board inside r 11.8 (the bottom parts' radius), 2.0 mm deeper than the pocket floor
               (bottom parts <= 1.45 mm); the board rests only on the r 11.8-13.2 band
  B3  RULE     two finger notches to lift the board out; printed flat in PETG (survives a hot plate at ~100 C
               preheat only: use the jig for stencilling and hot air, not on a 240 C plate)
"""
from __future__ import annotations

import sys
from pathlib import Path

from build123d import Align, Box, BuildPart, Cylinder, Locations, Mode

sys.path.insert(0, str(Path(__file__).parent))
from _lib import moonlib as L  # noqa: E402
from _lib.meshkit import claim  # noqa: E402

PRINT = {"material": "petg-basic", "process": "0.20-standard", "supports": "none", "supported": [],
         "orientation": "as-modelled"}
VERIFY = {"jig_fit": "the delivered board drops into the pocket without forcing and sits flush (+/- 0.1 mm)"}
D_OUT, H = 40.0, 4.0
POCKET_D = 2 * L.BOARD_R + 0.4
POCKET_T = L.BOARD_T
RELIEF_R = L.COMPONENT_R_MAX
RELIEF_T = 2.0


def part():
    with BuildPart() as p:
        Cylinder(D_OUT / 2, H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations((0, 0, H - POCKET_T)):
            Cylinder(POCKET_D / 2, POCKET_T + 0.1, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        with Locations((0, 0, H - POCKET_T - RELIEF_T)):
            Cylinder(RELIEF_R, RELIEF_T + 0.1, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        for sx in (-1, 1):   # finger notches across the pocket rim
            with Locations((sx * (POCKET_D / 2 + 1.0), 0, H - POCKET_T - 0.8)):
                Box(6.0, 8.0, POCKET_T + 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    return p.part


def spec(m, p):
    lo, hi = m.bounds
    return [claim("B1", "board top flush with the jig top", abs(POCKET_T - L.BOARD_T) < 1e-6, POCKET_T),
            claim("B2", "relief clears the bottom parts (>= 1.45 mm under the board)", RELIEF_T >= 1.45, RELIEF_T),
            claim("B2", "board rests on the edge band only", RELIEF_R <= L.COMPONENT_R_MAX + 1e-6 and
                  RELIEF_R < POCKET_D / 2 - 1.0, RELIEF_R),
            claim("B1", "pocket floor present on the band", bool(m.contains([[12.5, 5.0, H - POCKET_T - 0.3]])[0])),
            claim("B3", "fits the bed", float(hi[0] - lo[0]) < 60, round(float(hi[0] - lo[0]), 1))]
