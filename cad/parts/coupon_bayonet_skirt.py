"""Bayonet coupon, skirt half (the moon's own PLA and process): the moon's exact lower part - skirt, grooves, entry
slots, clamp cone, bore and the bottom of the bowl, closed 0.7 mm above the step into the lithophane. Pair it
with coupon_bayonet_cup.

Requirements (newest last; never renumber):
  B1  RULE     geometry is cut from the real part (moon_shell.part()) - no copied numbers
  B2  RULE     (round3 R3-M3) printed in the moon's white PLA at 0.12 mm with the moon's walls/infill, skirt on the bed
               like the moon, so stiffness, friction, layer steps and the 0.15 mm slip match the real fit
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _lib import moonlib as L  # noqa: E402
from _lib.meshkit import as_manifold, claim  # noqa: E402
import moon_shell  # noqa: E402

PRINT = {"material": "pla-basic-white", "process": "0.12-fine", "supports": "none", "supported": [],
         "orientation": "as-modelled",
         "slicer_overrides": {"wall_loops": 6, "sparse_infill_density": "100%", "brim_type": "outer_only", "brim_width": 3}}
VERIFY = {"bayonet": "see coupon_bayonet_cup; record the turning feel and any whitening at the groove ends (M4)"}


CAP_TOP = L.Z_TRIM + 0.7     # moon frame: the coupon ends 0.7 mm above the exact part's step into the lithophane


def part():
    # the moon's exact lower part (skirt, grooves, slots, clamp cone, bore, the bottom of the inner bowl) with the
    # bowl and the 45 deg collar carried on up to CAP_TOP and closed flat: one revolve of the moon's own surfaces,
    # so the coupon has no seam or ledge of its own over the cone or the collar (round 3)
    return as_manifold(moon_shell.part(cap_top=CAP_TOP))


def spec(m, p):
    lo, hi = m.bounds
    v = m.mesh.vertices
    bed = v[v[:, 2] < 1e-3]                                   # the skirt's bottom face (the collar flares above it)
    od = 2 * float((bed[:, 0] ** 2 + bed[:, 1] ** 2).max() ** 0.5)
    return [claim("B1", "skirt bottom on the bed, its OD 25.3 mm", abs(lo[2]) < 1e-3 and abs(od - 2 * L.SKIRT_R_OUT) < 0.05,
                  round(od, 2))]
