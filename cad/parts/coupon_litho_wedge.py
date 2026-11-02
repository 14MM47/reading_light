"""Lithophane step wedge: seven 10 x 10 mm windows 0.6-3.0 mm thick in a 3.2 mm frame. Print in the moon's white
PLA at the moon's settings, hold it over the lit LED board, photograph/meter each step on each LED channel; feeds
LAMBDA in cad/tools/moon_preview.py and the T_MIN/T_MAX choice in _lib/moonlib.py.

Requirements (newest last; never renumber):
  B1  RULE     steps 0.6, 1.0, 1.4, 1.8, 2.2, 2.6, 3.0 mm; frame 3.2 mm; thinnest step >= 0.6 (3 lines at 0.2 mm)
"""
import sys
from pathlib import Path

from build123d import Align, Box, BuildPart, Locations, Mode

sys.path.insert(0, str(Path(__file__).parent))
from _lib.meshkit import claim  # noqa: E402

PRINT = {"material": "pla-basic-white", "process": "0.12-fine", "supports": "none", "supported": [],
         "orientation": "as-modelled",
         "overrides": {"wall_fail": {"value": 0.55, "why": "the 0.6 mm window is the deliberate thin end of a "
                                                        "transmission test, not a structural wall"}}}
VERIFY = {}
STEPS = [0.6, 1.0, 1.4, 1.8, 2.2, 2.6, 3.0]


def part():
    with BuildPart() as p:
        Box(7 * 12 + 2, 14, 3.2, align=(Align.MIN, Align.MIN, Align.MIN))
        for i, t in enumerate(STEPS):
            with Locations((2 + 12 * i, 2, t)):
                Box(10, 10, 3.2, align=(Align.MIN, Align.MIN, Align.MIN), mode=Mode.SUBTRACT)
    return p.part


def spec(m, p):
    return [claim("B1", "seven steps", len(STEPS) == 7)]
