"""Bayonet coupon, cup half (PETG, like the real cup): the top of the moon base cup with its pocket, land and lugs.
Pair it with coupon_bayonet_skirt (the moon's PLA). Drop an 18 mm disc (0.9 / 1.0 / 1.1 mm, the board's tolerance) or
an LED board and a moon_ring into the pocket, slide the skirt half over and turn it clockwise to lock (VERIFY M4/M5).

Requirements (newest last; never renumber):
  B1  RULE     geometry is cut from the real part (moon_base.part()) - no copied numbers
  B2  RULE     (round3 R3-M3) printed in the real cup's material and process (PETG, 0.16 mm), cut on one of the real
               cup's layer boundaries so its lug and land steps match the real cup's
"""
import math
import sys
from pathlib import Path

import manifold3d as mf

sys.path.insert(0, str(Path(__file__).parent))
from _lib.meshkit import as_manifold, claim  # noqa: E402
import moon_base  # noqa: E402

PRINT = {"material": "petg-basic", "process": "0.16-fine", "supports": "none", "supported": [], "orientation": "as-modelled"}
VERIFY = {"bayonet": "with coupon_bayonet_skirt: lugs enter, a clockwise 30 deg turn locks onto the ring without "
                     "forcing, with 0.9, 1.0 and 1.1 mm discs; no rattle (M4, M5)"}
LAYER = 0.16                                   # moon_base's layer height (PRINT process): first layer 0.2 is not
FIRST = 0.2                                    # one of them, so the boundaries sit at 0.2 + k * 0.16


def cut_z():
    """Highest real-cup layer boundary at least 1 mm under the moon's skirt bottom."""
    d = moon_base.dims()
    k = math.floor((d["moon_z0"] - 1.0 - FIRST) / LAYER)
    return FIRST + k * LAYER


def part():
    cup = as_manifold(moon_base.part())
    z0 = cut_z()
    keep = mf.Manifold.cube((100, 100, 50)).translate((-50, -50, z0))
    return (cup ^ keep).translate((0, 0, -z0))


def spec(m, p):
    lo, hi = m.bounds
    z0 = cut_z()
    phase = ((z0 - FIRST) / LAYER) % 1.0
    v = m.mesh.vertices
    r_max = float((v[:, 0] ** 2 + v[:, 1] ** 2).max() ** 0.5)
    return [claim("B1", "cup top on the bed, lugs included (lug OD 22.4)", abs(lo[2]) < 1e-6 and 2 * r_max > 22.3,
                  round(2 * r_max, 2)),
            claim("B2", "cut on a real-cup layer boundary", min(phase, 1 - phase) < 1e-6, round(z0, 3))]
