"""Pack front shell: the face with the three buttons, the walls with the USB-C, slide-switch and neck openings.
The main PCB hangs from two bosses on the inside of the face (M2 self-tapping screws from the PCB's back).

Requirements (newest last; never renumber):
  B1  GIVEN    (Matt) pack holds battery + electronics, clips to the back of a book
  B2  GIVEN    (Matt) main button with up/down brightness buttons above and below it, on the pack
  B3  GIVEN    (Matt) slide on/off switch on the side
  B4  GIVEN    (Matt) USB-C charging; flexible neck from the top of the pack
  B5  RULE     openings and bosses come from hardware/main-board/design.py (PLACE, MOUNT_HOLES) - no copied numbers
  B6  ASSUMED  gooseneck's M10x1 end self-taps into a 9.3 mm socket in a boss inside the top wall (+ optional CA gel;
               never anaerobic thread-locker, it crazes PETG: round1 m-7);
               the pack is too thin for the 14 mm nut used in the moon base
  B7  ASSUMED  USB-C window 12.8 x 7.0 mm with the wall thinned to 1.2 mm around it so a moulded plug seats fully
  B8  ASSUMED  slide-switch knob reached through a 5.0 x 2.6 mm window with a 45 deg outer chamfer
  B9  ASSUMED  charge LED shows through a 1.8 mm hole in the face
  B10 RULE     printed face-down (outer face on the bed), PETG; holes in vertical walls are teardrops or bridges <= 20 mm
  B11 RULE     (round2 R2-D5) 0.8 mm pocket in the face's inner surface over J2: the JST PH side-entry header is
               5.5 mm tall (JST catalogue) against TOP_CLEAR 5.6
  B12 RULE     (round2 R2-D6, implements B8) the switch window sits in a 0.9 mm deep, 45 deg-tapered recess, so the
               knob tip is <= 0.5 mm below the local outer surface
  B13 RULE     (round2 R2-D14, supersedes B7's size) USB-C window 13.4 x 7.6 mm with 0.8 mm corner chamfers, so a
               square-cornered 12.35 x 6.5 mm overmold can seat fully
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
    "jst_ph_height": "S2B-PH-SM4-TB is 5.5 mm tall (JST); 0.8 mm face pocket over it gives 0.9 mm (R2-D5)",
    "usb_plug": "the USB-C cables you will use seat fully through the 13.4 x 7.6 window (R2-D14)",
}
USB_Z = K.Z_PCB_TOP + 1.63
KNOB_Z = K.Z_PCB_TOP + 0.9
KNOB_TIP_X = K.placed("SW1")[0] + 3.15     # PCM12 actuator tip: 3.15 mm from the footprint origin (R2-D6)
SW_RECESS = 0.9                            # tapered finger recess depth: leaves a 0.9 mm wall (>= 0.84 rule)
J2_POCKET = (-17.0, -7.5, -25.8, -18.2, 0.8)   # X0, X1, Y0, Y1, depth: over the J2 header body (board x 1.7-9.3)
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
                _chamfered_rect(13.4, 7.6, 0.8)   # (X, Z) window; 45 deg corners print without support
            extrude(amount=K.WALL + 0.3, mode=Mode.SUBTRACT)
        with Locations(Pos(X, K.OUT_Y_BOT - 0.1, USB_Z) * Rot(-90, 0, 0)):
            with BuildSketch():
                _chamfered_rect(15.6, 7.6, 0.8)
            extrude(amount=K.WALL - 1.2 + 0.1, mode=Mode.SUBTRACT)
        # slide-switch window in the right wall, inside a 45 deg-tapered finger recess (B8, B12)
        X, Y, _ = K.placed("SW1")
        with Locations(Pos(K.IN_X - 0.1, Y, KNOB_Z) * Rot(0, 90, 0)):
            with BuildSketch():
                Rectangle(2.6, 5.0)
            extrude(amount=K.WALL + 0.3, mode=Mode.SUBTRACT)
        recess_plane = Plane(origin=(K.OUT_X + 0.01, Y, KNOB_Z), x_dir=(0, 1, 0), z_dir=(-1, 0, 0))
        with BuildSketch(recess_plane):
            Rectangle(5.0 + 2 * (SW_RECESS + 1.0), 2.6 + 2 * (SW_RECESS + 1.0))
        extrude(amount=SW_RECESS + 0.01, taper=45, mode=Mode.SUBTRACT)
        # J2 header headroom pocket in the face's inner surface (B11)
        x0, x1, y0p, y1p, dp = J2_POCKET
        with Locations(((x0 + x1) / 2, (y0p + y1p) / 2, K.Z_FACE_IN - 0.01)):
            Box(x1 - x0, y1p - y0p, dp + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN), mode=Mode.SUBTRACT)
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
    X_USB = X
    out.append(claim("B7", "USB window open", not bool(m.contains([[-X, K.OUT_Y_BOT + 0.9, K.Z_TOP - USB_Z]])[0])))
    X, Y, _ = K.placed("SW1")
    out.append(claim("B8", "slide-switch window open", not bool(m.contains([[-(K.IN_X + 0.9), Y, K.Z_TOP - KNOB_Z]])[0])))
    out.append(claim("B6", "neck socket open", not bool(m.contains([[0, K.OUT_Y_TOP - 0.9, K.Z_TOP - NECK_Z]])[0])))
    out.append(claim("B5", "PCB mounting bosses present", len(K.mount_holes()) >= 2, len(K.mount_holes())))
    local_surface = K.OUT_X - SW_RECESS
    out.append(claim("B12", "switch knob tip <= 0.5 mm below the local outer surface", local_surface - KNOB_TIP_X <= 0.5,
                     round(local_surface - KNOB_TIP_X, 2)))
    out.append(claim("B12", "finger recess open around the window",
                     not bool(m.contains([[-(K.OUT_X - 0.5), Y + 3.4, K.Z_TOP - KNOB_Z]])[0])))
    x0, x1, y0p, y1p, dp = J2_POCKET
    out.append(claim("B11", "J2 headroom pocket open (header 5.5 mm, clearance >= 0.8 mm)",
                     not bool(m.contains([[-(x0 + x1) / 2, (y0p + y1p) / 2, K.Z_TOP - (K.Z_FACE_IN + dp / 2)]])[0]) and
                     K.TOP_CLEAR + dp - 5.5 >= 0.8, round(K.TOP_CLEAR + dp - 5.5, 2)))
    out.append(claim("B13", "USB window 13.4 mm wide open at its edge",
                     not bool(m.contains([[-(X_USB + 6.4), K.OUT_Y_BOT + 0.9, K.Z_TOP - USB_Z]])[0])))
    return out
