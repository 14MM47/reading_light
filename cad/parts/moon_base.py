"""Moon base cup: holds the 18 mm LED board facing up into the moon, carries the bayonet lugs the moon locks onto,
and screws onto the gooseneck's M10x1 end with a captured nut. v0.2: the cup sits inside the moon's skirt (a slim
stem, 20.8 mm body) instead of wrapping round the moon (38.7 mm in v0.1).

Requirements (newest last; never renumber):
  B1  GIVEN    (Matt) LEDs in the base of the moon at the top of the neck
  B2  GIVEN    (Matt) pre-made metal bendable arm (gooseneck); chosen: 120 mm, 10 mm OD, M10x1 ends, 6.8 mm bore
  B3  RULE     (optics model, v0.1 head) LED emitters 2.9 mm below the moon's opening plane (superseded by B12)
  B9  RULE     (thermal review) a 0.6 mm PETG clamp ring (moon_ring.py) sits between the board edge and the PLA moon:
               the PLA never touches the board, which runs up to ~45-55 C (v0.2: 0.8 mm, moon_ring B3)
  B4  RULE     (LED board design) the board's edge band (v0.2: r 8-9 mm) is clamped between a ledge and the ring; parts
               on the board's underside stay inside r 7.8 mm and need 1.5 mm of height
  B5  ASSUMED  (v0.1) bayonet: 3 vertical entry slots + 30 deg grooves in the cup (superseded by B13)
  B6  ASSUMED  the gooseneck's threaded end passes up through the floor and is held by an M10x1 hex nut sitting
               in a hex socket on the floor (anti-rotation); a drop of CA gel on the thread (no anaerobic
               thread-locker: round1 m-7)
  B7  ASSUMED  the 4-wire cable runs up the gooseneck bore, through the nut, to the board's underside pads
  B8  RULE     printed upright (floor on the bed) in PETG (warmer than PLA: sits against the LED board)
  B10 RULE     (round2 R2-D3) >= 4.5 mm free height between the nut top and the board underside: the wires leave the
               gooseneck bore above the nut and turn to the pads; the thread must end at or below the nut top (VERIFY)
  B11 RULE     (round2 R2-D15) the board is located by the pocket wall but its top stands proud of the cup, so only the
               ring bears on it and the bayonet's cam preloads it (round 3: the preload's spring is B17)
  B12 RULE     (corrected optics model, v0.2) white emitters 1.2 mm below the moon's opening plane (board top 1.9 mm)
  B13 ASSUMED  (v0.2) bayonet turned inside out: 3 lugs on the cup's outside (3 mm wide, 0.8 mm radial, 45 deg top and
               bottom so they print without support) lock into grooves inside the moon's skirt (moon_shell B15)
  B14 RULE     (v0.2) the cup's rim is a flat land (>= 0.84 mm, 0.1 under the board top) and a 45 deg bevel 0.25 mm
               under the moon's clamp cone (moon_shell B16); the lug tops lie on the bevel's cone (round 3: land 0.4
               under the board top, B17; bevel 0.35 mm, GAP_45)
  B15 RULE     (v0.2) the cavity under the board (r 8.35) clears the nut socket's corners: no ceiling to print
  B16 RULE     (round3 R3-M4) the floor is jammed between the socket nut and a second M10x1 nut + washer underneath, so
               the cup cannot turn or slide on the thread (the gooseneck end has no shoulder: VERIFY M1); the thread
               needs >= NUT_T + FLOOR_T + WASHER_T + NUT_T = 9 mm at the moon end
  B17 RULE     (round3 R3-M1) the clamp is a designed spring: the land sits LAND_DROP (0.4) under the board top, so the
               ring's overhang can roll down about the board's top edge; travel at the cone 0.23-0.39 mm for a 0.9-1.1
               board covers the moon's preload LOCK_OFFSET + (board - 1.0) = 0.05-0.25 (moon_shell B18)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import manifold3d as mf
from build123d import Align, BuildPart, BuildSketch, Cylinder, Locations, Mode, Plane, Pos, RegularPolygon, extrude

sys.path.insert(0, str(Path(__file__).parent))
from _lib import moonlib as L  # noqa: E402
from _lib.meshkit import as_manifold, claim  # noqa: E402

PRINT = {
    "material": "petg-basic",
    "process": "0.16-fine",
    "supports": "none",
    "supported": [],
    "orientation": "as-modelled",
}
VERIFY = {
    "NUT_AF": f"{L.NUT_AF} mm across flats, {L.NUT_T} mm thick: measure the nut supplied with the gooseneck",
    "NECK_THREAD_D": "M10x1 thread on the gooseneck ends (seller listing): measure with calipers",
    "BOARD_T": "LED board thickness 1.0 mm as ordered",
    "thread_protrusion": "gooseneck thread must not stand more than 0.5 mm above the nut top: cut/file it to length "
                         "BEFORE the cable goes in (R2-D3, R3-M5)",
    "thread_length": f"moon-end thread >= {L.THREAD_LEN_MIN:.0f} mm (lower nut + washer + floor + socket nut, B16)",
    "shoulder": "if the gooseneck end has a shoulder >= 12 mm, the lower nut may be replaced by it (B16)",
}


def dims():
    """Heights in the cup frame (bed z = 0)."""
    floor_top = L.FLOOR_T
    nut_top = floor_top + L.NUT_T
    ledge_z = nut_top + L.UNDER_BOARD_DEPTH          # board bottom rests here
    board_top = ledge_z + L.BOARD_T
    ring_top = board_top + L.RING_T
    rim_in_z = L.cup_z(L.Z_LAND)                       # flat land on top of the pocket wall ...
    rim_out_z = L.cup_z(L.TOP_C - L.CUP_R)            # ... then a 45 deg bevel down to the cup's outer wall
    cut_z = L.cup_z(L.Z_CUT)                          # moon's opening plane
    moon_z0 = L.cup_z(L.Z_SKIRT_BOT)                  # where the moon's print frame z = 0 (skirt bottom) sits
    return dict(floor_top=floor_top, nut_top=nut_top, ledge_z=ledge_z, board_top=board_top, ring_top=ring_top,
                rim_in_z=rim_in_z, rim_out_z=rim_out_z, rim_z=rim_in_z, cut_z=cut_z, moon_z0=moon_z0)


def _revolved(profile, a0_deg, span_deg):
    segs = max(8, int(abs(span_deg) / 1.5))
    pts = [(float(r), float(z)) for r, z in profile]
    area2 = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    cs = mf.CrossSection([pts if area2 > 0 else pts[::-1]])
    return mf.Manifold.revolve(cs, segs, float(span_deg)).rotate((0.0, 0.0, float(a0_deg)))


def part():
    d = dims()
    ch = 0.8                                          # 45 deg chamfer at the bed edge
    body = _revolved([(L.NECK_HOLE_R, 0.0), (L.CUP_R - ch, 0.0), (L.CUP_R, ch), (L.CUP_R, d["rim_out_z"]),
                      (L.LAND_R_OUT, d["rim_in_z"]), (L.POCKET_R, d["rim_in_z"]), (L.POCKET_R, d["ledge_z"]),
                      (L.BOARD_LEDGE_IN_R, d["ledge_z"]),
                      (L.BOARD_LEDGE_IN_R, d["nut_top"]), (L.NECK_HOLE_R, d["nut_top"])], 0.0, 360.0)
    span = math.degrees(L.LUG_W / L.LUG_R_OUT)
    for a in L.LUG_ANGLES:
        body = body + _revolved(L.lug_profile_cup(), a - span / 2, span)
    # hex socket for the M10x1 nut on the floor (anti-rotation), 0.2 mm clearance across flats; its corners
    # (r 8.31) stay inside the cavity radius above (r 8.35), so the socket's top is open: no ceiling (B15).
    # The prism runs 0.3 mm up into the cavity so no face is coplanar with the cavity floor.
    with BuildPart() as hx:
        with BuildSketch(Plane.XY.offset(d["floor_top"])):
            RegularPolygon((L.NUT_AF + 0.4) / math.sqrt(3), 6, major_radius=True)
        extrude(amount=L.NUT_T + 0.3)
    return body - as_manifold(hx.part)


def context(p):
    d = dims()
    board = Pos(0, 0, d["ledge_z"]) * Cylinder(L.BOARD_R, L.BOARD_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    nut = Pos(0, 0, d["floor_top"]) * extrude(RegularPolygon(L.NUT_AF / math.sqrt(3), 6, major_radius=True),
                                              amount=L.NUT_T)
    washer = Pos(0, 0, -L.WASHER_T) * Cylinder(10.0, L.WASHER_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    nut_lo = Pos(0, 0, -L.WASHER_T - L.NUT_T) * extrude(RegularPolygon(L.NUT_AF / math.sqrt(3), 6, major_radius=True),
                                                        amount=L.NUT_T)
    return {"led_board": board, "nut": nut, "washer": washer, "nut_lower": nut_lo}


def spec(m, p):
    d = dims()
    lo, hi = m.bounds
    out = [claim("B12", "white emitters 1.2 mm below the opening plane (board top 1.9 mm below)",
                 abs(d["cut_z"] - d["board_top"] - (L.LED_DEPTH + L.EMITTER_H)) < 1e-6,
                 round(d["cut_z"] - d["board_top"], 3))]
    out.append(claim("B4", "pocket radius = board radius + 0.2", abs(L.POCKET_R - L.BOARD_R - L.FIT_PCB) < 1e-6, L.POCKET_R))
    out.append(claim("B4", "ledge inner radius clears bottom parts (>= 7.8)", L.BOARD_LEDGE_IN_R >= L.COMPONENT_R_MAX,
                     L.BOARD_LEDGE_IN_R))
    out.append(claim("B6", "floor hole passes the M10 thread", L.NECK_HOLE_R * 2 >= L.NECK_THREAD_D + 0.4, L.NECK_HOLE_R * 2))
    out.append(claim("B8", "outer diameter (body 20.8 mm, lugs 22.4 mm)", 20 < 2 * L.CUP_R < 22 and 2 * hi[0] < 23,
                     round(float(2 * hi[0]), 2)))
    r_probe = (L.BOARD_LEDGE_IN_R + L.POCKET_R) / 2
    out.append(claim("B4", "ledge present under the board edge", bool(m.contains([[r_probe, 0, d["ledge_z"] - 0.3]])[0])))
    out.append(claim("B10", ">= 4.5 mm between the nut top and the board underside", d["ledge_z"] - d["nut_top"] >= 4.5 - 1e-6,
                     round(d["ledge_z"] - d["nut_top"], 2)))
    out.append(claim("B11", "pocket wall locates the board, board top proud of the cup rim",
                     d["ledge_z"] + 0.5 < d["rim_in_z"] < d["board_top"], round(d["rim_in_z"] - d["ledge_z"], 3)))
    out.append(claim("B13", "3 lugs, 0.8 mm radial", abs(L.LUG_R_OUT - L.CUP_R - 0.8) < 1e-9 and L.LUG_N == 3,
                     round(L.LUG_R_OUT - L.CUP_R, 3)))
    a = math.radians(L.LUG_ANGLES[0])
    zl = (L.cup_z(L.Z_LUG_FACE_TOP) + L.cup_z(L.Z_LUG_FACE_BOT)) / 2
    out.append(claim("B13", "lug present", bool(m.contains([[(L.LUG_R_OUT - 0.2) * math.cos(a),
                                                            (L.LUG_R_OUT - 0.2) * math.sin(a), zl]])[0])))
    out.append(claim("B14", "rim bevel GAP_45 (0.35 mm) under the moon's clamp cone",
                     abs((L.CONE_C - L.TOP_C) / math.sqrt(2) - L.GAP_45) < 1e-9 and abs(L.GAP_45 - 0.35) < 1e-9))
    out.append(claim("B14", "rim land >= 0.84 mm wide", L.LAND_R_OUT - L.POCKET_R >= 0.84, round(L.LAND_R_OUT - L.POCKET_R, 3)))
    out.append(claim("B17", "land LAND_DROP under the board top (the ring's roll gap)",
                     abs(d["board_top"] - d["rim_in_z"] - L.LAND_DROP) < 1e-9, round(d["board_top"] - d["rim_in_z"], 3)))
    closure = [(t, round(L.ring_preload(t), 3), round(L.ring_travel(t), 3)) for t in (0.9, 1.0, 1.1)]
    out.append(claim("B17", "preload 0.03 mm .. roll travel for a 0.9 / 1.0 / 1.1 mm board",
                     all(0.03 <= pre <= trav for _, pre, trav in closure), closure))
    out.append(claim("B17", "the ring's overhang lands on the land, not the bevel", L.RING_R_OUT < L.LAND_R_OUT - 0.1,
                     round(L.LAND_R_OUT - L.RING_R_OUT, 3)))
    out.append(claim("B15", "nut socket corners inside the cavity radius", (L.NUT_AF + 0.4) / math.sqrt(3) < L.BOARD_LEDGE_IN_R,
                     round((L.NUT_AF + 0.4) / math.sqrt(3), 3)))
    return out
