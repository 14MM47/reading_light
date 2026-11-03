"""Bayonet + LED-board pocket coupon: the top of the moon base cup (with its lugs) and the moon's skirt ring (with the
grooves and the clamp cone), printed side by side. Drop an LED board (or an 18 mm x 1.0 mm disc) and the PETG ring
into the pocket, slide the skirt over the cup and twist-lock it, before printing the 50 mm moon.

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
    z0 = d["moon_z0"] - 1.0                                       # from just below the moon's skirt bottom
    keep = mf.Manifold.cube((100, 100, 50)).translate((-50, -50, z0))
    top = (cup ^ keep).translate((-17, 0, -z0))
    # the moon's exact lower part, cut at the opening plane, with a 1 mm cap standing in for the lithophane above
    # (alone, the clamp cone and the overlap band end in knife edges at the cut plane)
    zc = L.Z_CUT + moon_shell.SHIFT
    # cut 0.05 under the cut plane: the skirt profile has a ring of vertices exactly at it
    low = as_manifold(moon_shell.part()) ^ mf.Manifold.cube((60, 60, zc - 0.05)).translate((-30, -30, 0))
    r_in = L.R_RIDGE + 0.4                                      # a 0.4 mm step: no coincident edge with the cone
    r_out = L.COLLAR_K + L.Z_CUT - 0.35                         # inside the collar at the cap's bottom (no ledge)
    cap = mf.Manifold.cylinder(1.0, r_out, r_out, 180).translate((0, 0, zc - 0.3)) - \
        mf.Manifold.cylinder(1.4, r_in, r_in, 180).translate((0, 0, zc - 0.5))
    skirt = (low + cap).translate((17, 0, 0))
    return top + skirt


def spec(m, p):
    lo, hi = m.bounds
    return [claim("B1", "two pieces fit the bed", (hi[0] - lo[0]) < 90, round(float(hi[0] - lo[0]), 1))]
