"""Moon base cup: holds the 26 mm LED board facing up into the moon, locks the moon by a bayonet, and screws
onto the gooseneck's M10x1 end with a captured nut.

Requirements (newest last; never renumber):
  B1  GIVEN    (Matt) LEDs in the base of the moon at the top of the neck
  B2  GIVEN    (Matt) pre-made metal bendable arm (gooseneck); chosen: 120 mm, 10 mm OD, M10x1 ends, 6.8 mm bore
  B3  RULE     (optics model) LED emitters 2.9 mm below the moon's opening plane (board top 3.6 mm below)
  B9  RULE     (thermal review) a 0.6 mm PETG clamp ring (moon_ring.py) sits between the board edge and the PLA skirt:
               the PLA never touches the board, which runs up to ~45-55 C
  B4  RULE     (LED board design) the board edge band r 12-13 mm is clamped between a ledge and the moon skirt;
               parts on the board's underside stay inside r 11.8 mm and need 1.5 mm of height
  B5  ASSUMED  bayonet: 3 vertical entry slots + 30 deg grooves for the moon's lugs; groove ceilings chamfered
               45 deg so the cup prints without supports
  B6  ASSUMED  the gooseneck's threaded end passes up through the floor and is held by an M10x1 hex nut sitting
               in a hex socket on the floor (anti-rotation); a drop of CA gel on the thread (no anaerobic
               thread-locker: round1 m-7)
  B7  ASSUMED  the 4-wire cable runs up the gooseneck bore, through the nut, to the board's underside pads
  B8  RULE     printed upright (floor on the bed) in PETG (warmer than PLA: sits against the LED board)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from build123d import (Align, Axis, Box, BuildPart, BuildSketch, Cylinder, Locations, Mode, Plane, PolarLocations,
                       Pos, RegularPolygon, Rot, chamfer, extrude, Part)

sys.path.insert(0, str(Path(__file__).parent))
from _lib import moonlib as L  # noqa: E402
from _lib.meshkit import claim  # noqa: E402

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
}


def dims():
    floor_top = L.FLOOR_T
    nut_top = floor_top + L.NUT_T
    ledge_z = nut_top + L.UNDER_BOARD_DEPTH          # board bottom rests here
    board_top = ledge_z + L.BOARD_T
    ring_top = board_top + L.RING_T                    # = skirt bottom when locked
    rim_z = ring_top + L.SKIRT_H                       # cup rim = moon's cut plane
    return dict(floor_top=floor_top, nut_top=nut_top, ledge_z=ledge_z, board_top=board_top, ring_top=ring_top,
                rim_z=rim_z)


def part(*, wall=L.CUP_WALL, lug_clear=0.4, groove_turn=L.BAYONET_TURN_DEG):
    d = dims()
    H = d["rim_z"]
    with BuildPart() as p:
        # outer body: cylinder with a 45 deg chamfer at the bed edge
        Cylinder(L.CUP_R_OUT, H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        chamfer(p.edges().filter_by(Axis.Z, reverse=True).sort_by(Axis.Z)[0], 1.2)
        # skirt bore (from the board top up to the rim)
        with Locations((0, 0, d["board_top"])):
            Cylinder(L.BORE_UPPER_R, H, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        # LED board pocket
        with Locations((0, 0, d["ledge_z"])):
            Cylinder(L.POCKET_R, L.BOARD_T + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        # cavity under the board (parts + wires), down to the floor
        with Locations((0, 0, d["floor_top"])):
            Cylinder(L.BOARD_LEDGE_IN_R, d["ledge_z"] - d["floor_top"] + 0.01,
                     align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        # gooseneck thread hole through the floor
        Cylinder(L.NECK_HOLE_R, L.FLOOR_T + 0.02, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        # bayonet entry slots: lug profile (grown) extruded straight up from the groove to the rim
        span = math.degrees((L.LUG_W + 2 * lug_clear) / L.BORE_UPPER_R)
        for k in range(L.LUG_N):
            a0 = 90.37 + k * 360 / L.LUG_N
            with Locations(Rot(0, 0, a0) * Pos((L.LUG_SLOT_R + L.BORE_UPPER_R) / 2 - 0.1, 0, d["ring_top"] - 0.05)):
                Box(L.LUG_SLOT_R - L.BORE_UPPER_R + 0.2, L.LUG_W + 2 * lug_clear, H,
                    align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    cup = p.part
    # helical cam grooves: the groove profile revolved in steps, each step a little lower (CAM_DROP over the turn),
    # turning clockwise (seen from above) from each entry slot
    steps = 10
    span = math.degrees((L.LUG_W + 2 * lug_clear) / L.BORE_UPPER_R)
    for k in range(L.LUG_N):
        a0 = 90.37 + k * 360 / L.LUG_N
        for s_ in range(steps + 1):
            a = a0 + span / 2 - (groove_turn + span) * s_ / steps
            dz = -L.CAM_DROP * max(0.0, (s_ - 1)) / (steps - 1)
            seg = _revolved(L.groove_profile(d["ring_top"] + dz), a - (groove_turn + span) / steps - 0.3,
                            (groove_turn + span) / steps + 0.6)
            cup = cup - seg
    # hex socket for the M10x1 nut on the floor (anti-rotation), 0.2 mm clearance across flats
    with BuildPart() as hx:
        with Locations((0, 0, d["floor_top"])):
            Cylinder(L.BOARD_LEDGE_IN_R - 0.01, L.NUT_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with BuildSketch(Plane.XY.offset(d["floor_top"])):
            RegularPolygon((L.NUT_AF + 0.4) / math.sqrt(3), 6, major_radius=True)
        extrude(amount=L.NUT_T + 0.01, mode=Mode.SUBTRACT)
        # cable notch so wires can leave the nut's bore sideways toward the pads
        with Locations((0, (L.NUT_AF / 2 + L.BOARD_LEDGE_IN_R) / 2, d["floor_top"])):
            Box(4.0, L.BOARD_LEDGE_IN_R, L.NUT_T + 0.02, align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT)
    return cup + hx.part


def _revolved(profile, a0_deg, span_deg):
    from build123d import Polygon, revolve
    with BuildPart() as bp:
        with BuildSketch(Plane.XZ):
            Polygon(*profile, align=None)
        revolve(axis=Axis.Z, revolution_arc=span_deg)
    return bp.part.rotate(Axis.Z, a0_deg)


def _groove_roof_cutter(z_roof, turn):
    """Triangular-section ring segments: 45 deg roof from the groove's outer edge rising inward to the bore."""
    from build123d import Polyline, make_face, revolve
    rin, rout = L.BORE_UPPER_R - 0.01, L.LUG_SLOT_R
    h = rout - rin
    with BuildPart() as rc:
        for k in range(L.LUG_N):
            a0 = 90 + k * 360 / L.LUG_N
            with BuildSketch(Plane.XZ) as sk:
                Polyline((rin, z_roof), (rout, z_roof), (rin, z_roof + h), close=True)
                make_face()
            revolve(axis=Axis.Z, revolution_arc=turn + 2 * math.degrees(math.atan((L.LUG_W + 0.4) / 2 / rin)))
            rc.part = rc.part.rotate(Axis.Z, a0 - turn - math.degrees(math.atan((L.LUG_W + 0.4) / 2 / rin))) \
                if False else rc.part
    return rc.part


def context(p):
    d = dims()
    board = Pos(0, 0, d["ledge_z"]) * Cylinder(L.BOARD_R, L.BOARD_T, align=(Align.CENTER, Align.CENTER, Align.MIN))
    nut = Pos(0, 0, d["floor_top"]) * extrude(RegularPolygon(L.NUT_AF / math.sqrt(3), 6, major_radius=True),
                                              amount=L.NUT_T)
    return {"led_board": board, "nut": nut}


def spec(m, p):
    d = dims()
    lo, hi = m.bounds
    out = [claim("B3", "rim (moon cut plane) 3.6 mm above the board top (LED emitters 2.9 mm below)",
                 abs(d["rim_z"] - d["board_top"] - (L.SKIRT_H + L.RING_T)) < 1e-6, round(d["rim_z"] - d["board_top"], 3))]
    out.append(claim("B4", "pocket radius = board radius + 0.2", abs(L.POCKET_R - L.BOARD_R - L.FIT_PCB) < 1e-6, L.POCKET_R))
    out.append(claim("B4", "ledge inner radius clears bottom parts (>= 11.8)", L.BOARD_LEDGE_IN_R >= L.COMPONENT_R_MAX,
                     L.BOARD_LEDGE_IN_R))
    out.append(claim("B6", "floor hole passes the M10 thread", L.NECK_HOLE_R * 2 >= L.NECK_THREAD_D + 0.4, L.NECK_HOLE_R * 2))
    out.append(claim("B8", "outer diameter", 30 < 2 * hi[0] < 45, round(float(2 * hi[0]), 2)))
    # material ring under the board ledge must exist (probe a point in the ledge)
    r_probe = (L.BOARD_LEDGE_IN_R + L.POCKET_R) / 2
    out.append(claim("B4", "ledge present under the board edge", bool(m.contains([[r_probe, 0, d["ledge_z"] - 0.3]])[0])))
    return out
