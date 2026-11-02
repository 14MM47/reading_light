"""Slip-on book clip: a PETG cantilever along the back of the pack. The book's back cover slides between the arm's
bump and the pack; the arm's spring holds it.

Requirements (newest last; never renumber):
  B1  GIVEN    (Matt) the pack clips onto the back of the book with a slip-on clip
  B2  ASSUMED  grips covers 0.3-5 mm thick (paperback cover to hardback board + a few pages)
  B3  RULE     straight 2.4 mm arm, 18 mm wide, ~44 mm free length; a 1.3 mm bump near the tip with a 30 deg lead-in
               gives 0.3 mm preload against the pack; bending stress at 5 mm opening <= 20 MPa (PETG yield ~50)
  B4  RULE     printed flat (outer face on the bed) so layers run along the arm (strongest in bending)
  B5  ASSUMED  root block carries the two top M2 screws (M2 x 12) that also hold the back plate
"""
from __future__ import annotations

import sys
from pathlib import Path

from build123d import (Align, BuildPart, BuildSketch, Cylinder, Locations, Mode, Plane, Polygon, Pos, Box,
                       RectangleRounded, extrude, fillet, Axis)

sys.path.insert(0, str(Path(__file__).parent))
from _lib import packlib as K  # noqa: E402
from _lib.meshkit import claim  # noqa: E402

PRINT = {"material": "petg-basic", "process": "0.20-standard", "supports": "none", "supported": [],
         "orientation": "as-modelled (outer face on the bed)"}
VERIFY = {"grip": "clamp force ~5 N at 3 mm; check it holds the lamp on a hardback and a paperback without marking"}
E_PETG = 2000.0
ARM_T, ARM_W, GAP, BUMP = 2.4, 18.0, 1.0, 1.3
ROOT_T = ARM_T + GAP
ROOT_Y0, ROOT_Y1 = K.IN_Y_TOP - 9.0, K.IN_Y_TOP + K.WALL - 0.5
TIP_Y = -18.0


def arm_numbers(opening=5.0):
    L = ROOT_Y0 - (TIP_Y + 4.0)
    defl = opening + (BUMP - GAP)
    I = ARM_W * ARM_T ** 3 / 12
    sigma = 3 * E_PETG * ARM_T * defl / (2 * L ** 2)
    force = 3 * E_PETG * I * defl / L ** 3
    return L, sigma, force


def part():
    # built in print frame: outer face on the bed (z=0); +z toward the pack's back face
    with BuildPart() as p:
        # root block
        with Locations((0, (ROOT_Y0 + ROOT_Y1) / 2, 0)):
            Box(34.0, ROOT_Y1 - ROOT_Y0, ROOT_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # arm
        with Locations((0, (ROOT_Y0 + TIP_Y) / 2, 0)):
            Box(ARM_W, ROOT_Y0 - TIP_Y + 0.01, ARM_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # bump with lead-in near the tip (profile in the YZ plane, extruded across the width)
        with BuildSketch(Plane.YZ.offset(-ARM_W / 2)):
            Polygon((TIP_Y, ARM_T), (TIP_Y + 2.2, ARM_T + BUMP), (TIP_Y + 5.0, ARM_T + BUMP), (TIP_Y + 7.5, ARM_T),
                    align=None)
        extrude(amount=ARM_W)
        # screw holes + head counterbores (heads sit on the outer face)
        for x in (-13.0, 13.0):
            with Locations((x, K.IN_Y_TOP - 3.4, -0.1)):
                Cylinder(K.SCREW_CLEAR / 2, ROOT_T + 0.3, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
                Cylinder(2.2, 1.3, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    return p.part


def spec(m, p):
    L, sigma, force = arm_numbers(5.0)
    _, sigma3, force3 = arm_numbers(3.0)
    return [
        claim("B3", f"bending stress at 5 mm opening {sigma:.1f} MPa <= 20", sigma <= 20, round(sigma, 1)),
        claim("B3", f"clamp force at 3 mm cover {force3:.1f} N in 3-8 N", 3 <= force3 <= 8, round(force3, 1)),
        claim("B4", "printed flat, arm thickness 2.4 mm", abs(m.bounds[0][2]) < 1e-6, ARM_T),
    ]
