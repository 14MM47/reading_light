"""PETG clamp ring: sits on the LED board's edge band inside the base cup; the moon's skirt presses it down when the
bayonet is turned. Keeps the PLA moon off the warm board (thermal review: -8 K at the PLA).

Requirements (newest last; never renumber):
  B1  RULE     (thermal review) PETG, 0.6 mm thick (3 layers at 0.2), ID 24.0 mm (board band r 12-13) to OD = skirt OD - 0.2
  B2  RULE     printed flat
"""
import sys
from pathlib import Path

from build123d import Align, BuildPart, Cylinder, Mode

sys.path.insert(0, str(Path(__file__).parent))
from _lib import moonlib as L  # noqa: E402
from _lib.meshkit import claim  # noqa: E402

PRINT = {"material": "petg-basic", "process": "0.20-standard", "supports": "none", "supported": [], "orientation": "as-modelled",
         "overrides": {"wall_fail": {"value": 0.55, "why": "a 0.6 mm flat washer: its thickness is the design value (3 layers), "
                                                        "not a printed wall; it is clamped flat between the board and the skirt"}}}
VERIFY = {"ring_preload": "with the moon locked the board must not rattle; add a 0.2 mm shim ring if it does"}


def part():
    with BuildPart() as p:
        Cylinder(L.SKIRT_R_OUT - 0.1, L.RING_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        Cylinder(L.SKIRT_R_IN, L.RING_T + 0.2, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    return p.part


def spec(m, p):
    lo, hi = m.bounds
    return [claim("B1", "ring 0.6 mm thick", abs((hi[2] - lo[2]) - L.RING_T) < 1e-3, round(float(hi[2] - lo[2]), 3)),
            claim("B1", "covers the board band r 12-13", L.SKIRT_R_IN <= L.BOARD_CLAMP_IN and L.SKIRT_R_OUT - 0.1 > L.BOARD_R)]
