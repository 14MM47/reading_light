"""Bayonet + LED-board pocket coupon: the top 5 mm of the moon base cup and a skirt ring with the moon's lugs, printed
side by side. Twist-lock them, and drop an LED board (or a 26 mm x 1.0 mm disc) into the pocket before printing
the 50 mm moon.

Requirements (newest last; never renumber):
  B1  RULE     geometry is cut from the real parts (moon_base.part(), moon_shell.part()) - no copied numbers
"""
import sys
from pathlib import Path

import manifold3d as mf

sys.path.insert(0, str(Path(__file__).parent))
from _lib import moonlib as L  # noqa: E402
from _lib.meshkit import as_manifold, claim  # noqa: E402
import moon_base  # noqa: E402
import moon_shell  # noqa: E402

PRINT = {"material": "petg-basic", "process": "0.16-fine", "supports": "none", "supported": [], "orientation": "as-modelled"}
VERIFY = {"bayonet": "lugs enter, turn 30 deg and pull the skirt down onto a 1.0 mm disc without forcing"}


def part():
    d = moon_base.dims()
    cup = as_manifold(moon_base.part())
    z0 = d["ledge_z"] - 1.2
    keep = mf.Manifold.cube((100, 100, 50)).translate((-50, -50, z0))
    top = (cup ^ keep).translate((-22, 0, -z0))
    ring = as_manifold(moon_shell.part())                         # skirt + lugs, skirt bottom at z=0
    cap = mf.Manifold.cylinder(1.6, L.SKIRT_R_OUT, L.SKIRT_R_OUT, 120).translate((0, 0, L.SKIRT_H + 0.6 - 0.01)) - \
        mf.Manifold.cylinder(3.5, L.SKIRT_R_IN, L.SKIRT_R_IN, 120).translate((0, 0, L.SKIRT_H - 0.5))
    skirt = (ring + cap).translate((22, 0, 0))
    return top + skirt


def spec(m, p):
    lo, hi = m.bounds
    return [claim("B1", "two pieces fit the bed", (hi[0] - lo[0]) < 90, round(float(hi[0] - lo[0]), 1))]
