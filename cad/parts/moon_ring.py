"""PETG clamp ring: sits on the LED board's edge band; the moon's 45 deg clamp cone presses its chamfer down when
the bayonet is turned. Keeps the PLA moon off the warm board (thermal review: -8 K at the PLA).

Requirements (newest last; never renumber):
  B1  RULE     (thermal review) PETG, 0.6 mm thick (3 layers at 0.2), ID 24.0 mm (board band r 12-13) to OD = skirt OD - 0.2
               (v0.1; superseded by B3)
  B2  RULE     printed flat
  B3  RULE     (v0.2) 0.8 mm thick (4 layers), ID 16.0 mm (board band r 8-9), OD 19.8 mm, 0.4 mm x 45 deg chamfer on
               the top outer edge for the moon's clamp cone (moon_shell B16)
  B4  RULE     (round3 R3-M6) ID 16.4 mm: >= 0.4 mm clear of the white LEDs' bodies and pad corners (r 7.68 / 7.88)
               with the ring centred on the moon and the board floating in its pocket; it bears on r 8.2-9.0
  B5  RULE     (round3 R3-M1) printed at 0.12 mm layers (0.2 + 5 x 0.12 = 0.8): finer chamfer steps against the
               moon's cone; the ring's roll over the cup's land is the clamp spring (moon_base B17)
"""
import sys
from pathlib import Path

import manifold3d as mf

sys.path.insert(0, str(Path(__file__).parent))
from _lib import moonlib as L  # noqa: E402
from _lib.meshkit import claim  # noqa: E402

PRINT = {"material": "petg-basic", "process": "0.12-fine", "supports": "none", "supported": [], "orientation": "as-modelled",
         "overrides": {"wall_fail": {"value": 0.55, "why": "a 0.8 mm flat washer: its thickness is the design value (4 layers), "
                                                        "not a printed wall; it is clamped flat between the board and the moon"}}}
VERIFY = {"ring_preload": "with the moon locked the board must not rattle and the twist must not bind: tune "
                          "LOCK_OFFSET on the bayonet coupon (VERIFY M4/M5); no shims (they add rigid interference)"}


def part():
    c, t = L.RING_CHAMFER, L.RING_T
    prof = [(L.RING_R_IN, 0.0), (L.RING_R_OUT, 0.0), (L.RING_R_OUT, t - c), (L.RING_R_OUT - c, t), (L.RING_R_IN, t)]
    cs = mf.CrossSection([prof])
    return mf.Manifold.revolve(cs, 240, 360.0)


def spec(m, p):
    lo, hi = m.bounds
    return [claim("B3", "ring 0.8 mm thick", abs((hi[2] - lo[2]) - L.RING_T) < 1e-3, round(float(hi[2] - lo[2]), 3)),
            claim("B4", "bears on the board band (ID inside the board edge - 0.6, inside the clamp band)",
                  L.BOARD_CLAMP_IN <= L.RING_R_IN <= L.BOARD_R - 0.6 and L.RING_R_OUT > L.BOARD_R, L.RING_R_IN),
            claim("B4", "ID >= 0.4 mm clear of the LED bodies (COMPONENT_R_MAX)", L.RING_R_IN >= L.COMPONENT_R_MAX + 0.4,
                  round(L.RING_R_IN - L.COMPONENT_R_MAX, 3)),
            claim("B3", "OD 19.8 mm", abs(2 * float(hi[0]) - 19.8) < 0.05, round(2 * float(hi[0]), 2))]
