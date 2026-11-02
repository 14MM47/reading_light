"""Pack front shell: the face with the three buttons, the walls with the USB-C, slide-switch and neck openings.
The main PCB hangs from two bosses on the inside of the face (M2 self-tapping screws from the PCB's back).

Requirements (newest last; never renumber):
  B1  GIVEN    (Matt) pack holds battery + electronics, clips to the back of a book
  B2  GIVEN    (Matt) main button with up/down brightness buttons above and below it, on the pack
  B3  GIVEN    (Matt) slide on/off switch on the side
  B4  GIVEN    (Matt) USB-C charging; flexible neck from the top of the pack
  B5  RULE     openings and bosses come from hardware/main-board/design.py (PLACE, MOUNT_HOLES) - no copied numbers
  B6  ASSUMED  gooseneck's M10x1 end self-taps into a 9.3 mm socket in a boss inside the top wall (+ thread-locker);
               the pack is too thin for the 14 mm nut used in the moon base
  B7  ASSUMED  USB-C window 12.8 x 7.0 mm with the wall thinned to 1.2 mm around it so a moulded plug seats fully
  B8  ASSUMED  slide-switch knob reached through a 5.0 x 2.6 mm window with a 45 deg outer chamfer
  B9  ASSUMED  charge LED shows through a 1.8 mm hole in the face
  B10 RULE     printed face-down (outer face on the bed), PETG; holes in vertical walls are teardrops or bridges <= 20 mm
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from build123d import (Align, Axis, Box, BuildPart, BuildSketch, Cylinder, Locations, Mode, Plane, Pos, Rectangle,
                       RectangleRounded, Rot, extrude, fillet, chamfer, Circle, Polygon)

sys.path.insert(0, str(Path(__file__).parent))
from _lib import packlib as K  # noqa: E402
from _lib.meshkit import claim  # noqa: E402

PRINT = {"material": "petg-basic", "process": "0.20-standard", "supports": "none", "supported": [],
         "orientation": "as-modelled (face down: model is built in the pack frame then flipped in part())"}
VERIFY = {
    "usb_centre_height": "USB4125 receptacle centre 1.63 mm above the PCB top (GCT drawing: 3.26 mm tall body)",
    "pcm12_knob": "PCM12 knob centre ~0.9 mm above the PCB, protrudes ~1.0 mm past the board edge",
    "neck_socket": "9.3 mm socket for the M10x1 gooseneck thread: test on a coupon before printing the shell",
    "jst_ph_height": "S2B-PH-SM4-TB + plug height <= 5.2 mm (TOP_CLEAR 5.6 mm)",
}
USB_Z = K.Z_PCB_TOP + 1.63
KNOB_Z = K.Z_PCB_TOP + 0.9
NECK_Z = (K.Z_BACK + K.Z_FACE_IN) / 2


def _shell_body():
    w_out, w_in = 2 * K.OUT_X, 2 * K.IN_X
    h_out = K.OUT_Y_TOP - K.OUT_Y_BOT
    h_in = K.IN_Y_TOP - K.IN_Y_BOT
    yc_out = (K.OUT_Y_TOP + K.OUT_Y_BOT) / 2
    yc_in = (K.IN_Y_TOP + K.IN_Y_BOT) / 2
    with BuildPart() as p:
        with BuildSketch(Plane.XY):
            with Locations((0, yc_out)):
                RectangleRounded(w_out, h_out, K.CORNER_R)
        extrude(amount=K.Z_TOP)
        # chamfer on the front edge (the bed edge when printing face-down): 1.0 across x 1.2 up = 40 deg from vertical,
        # comfortably inside the 45 deg rule even where the rounded corners are tessellated
        front_edges = p.edges().filter_by(Axis.Z, reverse=True).group_by(Axis.Z)[-1]
        chamfer(front_edges, length=1.0, length2=1.2, reference=p.faces().sort_by(Axis.Z)[-1])
        with BuildSketch(Plane.XY):
            with Locations((0, yc_in)):
                RectangleRounded(w_in, h_in, K.CORNER_R - K.WALL)
        extrude(amount=K.Z_FACE_IN, mode=Mode.SUBTRACT)
    return p.part


def part(*, btn_hole=K.BTN_HOLE_D):
    s = _shell_body()
    with BuildPart() as p:
        p.part = s
        # button holes through the face
        for ref in ("SW2", "SW3", "SW4"):
            X, Y, _ = K.placed(ref)
            with Locations((X, Y, K.Z_FACE_IN - 0.1)):
                Cylinder(btn_hole / 2, K.FRONT_T + 0.3, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        # charge LED window
        X, Y, _ = K.placed("D2")
        with Locations((X, Y, K.Z_FACE_IN - 0.1)):
            Cylinder(0.9, K.FRONT_T + 0.3, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
        # USB-C window in the bottom wall + thinned wall pocket
        X, Y, _ = K.placed("J1")
        with Locations(Pos(X, K.OUT_Y_BOT - 0.1, USB_Z) * Rot(-90, 0, 0)):
            with BuildSketch():
                _chamfered_rect(12.8, 7.0, 1.5)   # (X, Z) window; 45 deg corners print without support
            extrude(amount=K.WALL + 0.3, mode=Mode.SUBTRACT)
        with Locations(Pos(X, K.OUT_Y_BOT - 0.1, USB_Z) * Rot(-90, 0, 0)):
            with BuildSketch():
                _chamfered_rect(15.0, 7.0, 1.5)
            extrude(amount=K.WALL - 1.2 + 0.1, mode=Mode.SUBTRACT)
        # slide-switch window in the right wall, with a 45 deg outer chamfer (a pyramid frustum cut)
        X, Y, _ = K.placed("SW1")
        with Locations(Pos(K.IN_X - 0.1, Y, KNOB_Z) * Rot(0, 90, 0)):
            with BuildSketch():
                Rectangle(2.6, 5.0)
            extrude(amount=K.WALL + 0.3, mode=Mode.SUBTRACT)
        # neck socket block inside the top wall (full cavity depth: vertical walls only, prints without overhangs)
        y0 = K.PCB_H / 2 + 5.0
        with Locations((0, (y0 + K.IN_Y_TOP) / 2 + 0.05, K.Z_BACK + 0.6)):
            Box(16.0, K.IN_Y_TOP - y0 + 0.1, K.Z_FACE_IN - K.Z_BACK - 0.6 + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # PCB mounting bosses (M2 pilot)
        for (X, Y) in K.mount_holes():
            with Locations((X, Y, K.Z_PCB_TOP + 0.05)):
                Cylinder(K.BOSS_D / 2, K.Z_FACE_IN - K.Z_PCB_TOP - 0.04, align=(Align.CENTER, Align.CENTER, Align.MIN))
                Cylinder(K.SCREW_PILOT / 2, K.Z_FACE_IN - K.Z_PCB_TOP - 0.6, align=(Align.CENTER, Align.CENTER, Align.MIN),
                         mode=Mode.SUBTRACT)
        # back-plate screw bosses in the neck region
        for X in (-13.0, 13.0):
            with Locations((X, K.IN_Y_TOP - 3.4, K.Z_BACK)):
                Cylinder(K.BOSS_D / 2 + 0.3, K.Z_FACE_IN - K.Z_BACK + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
                Cylinder(K.SCREW_PILOT / 2, 8.0, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
    shell = p.part
    # neck socket bore (teardrop toward the back so it prints face-down without support) through wall + boss
    bore = _teardrop_y(9.3 / 2, K.OUT_Y_TOP + 0.5, K.PCB_H / 2 + 4.0, NECK_Z)
    shell = shell - bore
    # bottom tab slots for the back plate (2 slots in the bottom wall's inner face)
    for X in (-9.0, 9.0):
        shell = shell - (Pos(X, K.IN_Y_BOT - 0.45 + 0.01, 1.1) * Box(6.4, 0.9, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    # flip to print orientation: face on the bed
    return shell.rotate(Axis.Y, 180).translate((0, 0, K.Z_TOP))


def _chamfered_rect(w, h, c):
    """Rectangle with 45 deg corner chamfers, centred, in the current BuildSketch."""
    a, b = w / 2, h / 2
    Polygon((-a + c, -b), (a - c, -b), (a, -b + c), (a, b - c), (a - c, b), (-a + c, b), (-a, b - c), (-a, -b + c))


def _teardrop_y(r, y0, y1, z):
    """Horizontal hole along Y with a 45 deg teardrop point toward -Z (toward the back)."""
    from build123d import Polyline, make_face
    L = y0 - y1
    with BuildPart() as t:
        with Locations(Pos(0, y1, z) * Rot(-90, 0, 0)):
            Cylinder(r, L, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with BuildSketch(Plane.XZ.offset(-y1)) as sk:
            Polygon((-r * math.sqrt(0.5), z - r * math.sqrt(0.5)), (r * math.sqrt(0.5), z - r * math.sqrt(0.5)),
                    (0, z - r * math.sqrt(2)), align=None)
        extrude(amount=-L)          # Plane.XZ's normal is -Y: negative amount runs toward +Y with the bore
    return t.part


def context(p):
    """PCB slab (as mounted) and the battery, both in print orientation, for clear_of checks."""
    with BuildPart() as b:
        with BuildSketch(Plane.XY.offset(K.Z_PCB_BOT)):
            RectangleRounded(K.PCB_W, K.PCB_H, K.MB.RC)
        extrude(amount=K.PCB_T)
    flip = lambda s: s.rotate(Axis.Y, 180).translate((0, 0, K.Z_TOP))  # noqa: E731
    return {"pcb": flip(b.part)}


def spec(m, p):
    lo, hi = m.bounds
    out = [claim("B1", "overall size within 45 x 80 x 20 mm", (hi[0] - lo[0]) <= 45 and (hi[1] - lo[1]) <= 80 and (hi[2] - lo[2]) <= 20,
                 [round(float(x), 1) for x in (hi - lo)])]
    for ref in ("SW2", "SW3", "SW4"):
        X, Y, _ = K.placed(ref)
        out.append(claim("B2", f"button hole open at {ref}", not bool(m.contains([[-X, Y, 0.9]])[0]), (round(X, 2), round(Y, 2))))
    X, Y, _ = K.placed("J1")
    out.append(claim("B7", "USB window open", not bool(m.contains([[-X, K.OUT_Y_BOT + 0.9, K.Z_TOP - USB_Z]])[0])))
    X, Y, _ = K.placed("SW1")
    out.append(claim("B8", "slide-switch window open", not bool(m.contains([[-(K.IN_X + 0.9), Y, K.Z_TOP - KNOB_Z]])[0])))
    out.append(claim("B6", "neck socket open", not bool(m.contains([[0, K.OUT_Y_TOP - 0.9, K.Z_TOP - NECK_Z]])[0])))
    out.append(claim("B5", "PCB mounting bosses present", len(K.mount_holes()) >= 2, len(K.mount_holes())))
    return out
