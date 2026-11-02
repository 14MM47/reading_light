"""Fit coupon: hole sizes to tune before printing the real parts (3dprint task A6 style).

Requirements (newest last; never renumber):
  B1  RULE     row A: gooseneck self-tap socket trials 9.1 / 9.2 / 9.3 / 9.4 / 9.5 mm, 8 mm deep (pack_front uses 9.3)
  B2  RULE     row B: button-cap holes 7.2 / 7.3 / 7.4 / 7.5 / 7.6 mm through 1.8 mm (pack_front uses 7.4)
  B3  RULE     raised index dots (1 dot = smallest) so the holes can be told apart
"""
from build123d import Align, Box, BuildPart, Cylinder, Locations, Mode
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib.meshkit import claim  # noqa: E402

PRINT = {"material": "petg-basic", "process": "0.20-standard", "supports": "none", "supported": [], "orientation": "as-modelled"}
VERIFY = {}
A = [9.1, 9.2, 9.3, 9.4, 9.5]
B = [7.2, 7.3, 7.4, 7.5, 7.6]


def part():
    with BuildPart() as p:
        Box(70, 36, 8, align=(Align.MIN, Align.MIN, Align.MIN))
        for i, d in enumerate(A):
            with Locations((8 + 13.5 * i, 26, -0.1)):
                Cylinder(d / 2, 8.2, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
            for k in range(i + 1):   # index dots on the top face (1 dot = smallest)
                with Locations((3.0 + 13.5 * i + 2.0 * k, 33.5, 8.0)):
                    Cylinder(0.6, 0.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
        for i, d in enumerate(B):
            with Locations((8 + 13.5 * i, 9, 6.2)):
                Cylinder(d / 2, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
            with Locations((8 + 13.5 * i, 9, -0.1)):
                Cylinder(d / 2 + 2.0, 6.3, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    return p.part


def spec(m, p):
    return [claim("B1", "five socket trials", len(A) == 5), claim("B2", "five button trials", len(B) == 5)]
