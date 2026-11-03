"""PETG clamp ring: sits on the LED board's edge band; the moon's 45 deg clamp cone presses its chamfer down when
the bayonet is turned. Keeps the PLA moon off the warm board (thermal review: -8 K at the PLA).

Requirements (newest last; never renumber):
  B1  RULE     (thermal review) PETG, 0.6 mm thick (3 layers at 0.2), ID 24.0 mm (board band r 12-13) to OD = skirt OD - 0.2
               (v0.1; superseded by B3)
  B2  RULE     printed flat
  B3  RULE     (v0.2) 0.8 mm thick (4 layers), ID 16.0 mm (board band r 8-9), OD 19.8 mm, 0.4 mm x 45 deg chamfer on
               the top outer edge for the moon's clamp cone (moon_shell B16)
"""
import sys
from pathlib import Path

import manifold3d as mf

sys.path.insert(0, str(Path(__file__).parent))
from _lib import moonlib as L  # noqa: E402
from _lib.meshkit import claim  # noqa: E402

PRINT = {"material": "petg-basic", "process": "0.20-standard", "supports": "none", "supported": [], "orientation": "as-modelled",
         "overrides": {"wall_fail": {"value": 0.55, "why": "a 0.8 mm flat washer: its thickness is the design value (4 layers), "
                                                        "not a printed wall; it is clamped flat between the board and the moon"}}}
VERIFY = {"ring_preload": "with the moon locked the board must not rattle; add a 0.2 mm shim ring if it does"}


def part():
    c, t = L.RING_CHAMFER, L.RING_T
    prof = [(L.RING_R_IN, 0.0), (L.RING_R_OUT, 0.0), (L.RING_R_OUT, t - c), (L.RING_R_OUT - c, t), (L.RING_R_IN, t)]
    cs = mf.CrossSection([prof])
    return mf.Manifold.revolve(cs, 240, 360.0)


def spec(m, p):
    lo, hi = m.bounds
    return [claim("B3", "ring 0.8 mm thick", abs((hi[2] - lo[2]) - L.RING_T) < 1e-3, round(float(hi[2] - lo[2]), 3)),
            claim("B3", "covers the board band r 8-9", L.RING_R_IN <= L.BOARD_CLAMP_IN + 1e-9 and L.RING_R_OUT > L.BOARD_R),
            claim("B3", "OD 19.8 mm", abs(2 * float(hi[0]) - 19.8) < 0.05, round(2 * float(hi[0]), 2))]
