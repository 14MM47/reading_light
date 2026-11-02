"""Shared dimensions for the moon, its LED base and the LED board (single source of truth, mm)."""
import math

R_OUT = 25.0            # outer radius at the thickest lithophane point (50 mm moon)
T_MIN = 0.9             # thinnest lithophane wall (>= 0.84 hard minimum: 2 perimeters)
T_MAX = 2.6             # thickest lithophane wall
R_IN = R_OUT - T_MAX    # smooth inner sphere
OPEN_R = 12.3           # radius of the bottom opening on the inner sphere (33.3 deg half-angle)
Z_CUT = -math.sqrt(R_IN ** 2 - OPEN_R ** 2)   # planar cut, sphere centre at z=0  (~ -19.34)
SKIRT_R_IN = 12.0       # a little inside the opening (avoids coincident boolean faces; wider clamp band)
SKIRT_R_OUT = 16.7      # full width of the moon's cut circle (45deg collar meets z_cut at r=16.64)
SKIRT_H = 2.5           # skirt below the cut plane; its bottom edge clamps the LED board
LUG_N = 3
LUG_W = 3.0             # tangential width
LUG_H = 1.2
LUG_R_OUT = 17.5
BAYONET_TURN_DEG = 30.0

BOARD_R = 13.0          # LED board radius (26 mm round), 1.0 mm thick FR4 (VERIFY with PCBWay order)
BOARD_T = 1.0
BOARD_CLAMP_IN = SKIRT_R_IN  # board edge band [SKIRT_R_IN, BOARD_R] is clamped: no copper/parts there
COMPONENT_R_MAX = 11.8   # all components inside this radius on both faces
LED_RING_R = 6.5

FIT_SLIP = 0.15          # radial slip-fit clearance printed part to printed part (VERIFY: fit coupon)
FIT_PCB = 0.2            # radial clearance PCB edge to printed bore


def opening_half_angle_deg():
    return math.degrees(math.asin(OPEN_R / R_IN))

# ---- LED base cup (PETG) ------------------------------------------------------------------------
CUP_WALL = 1.6
BORE_UPPER_R = SKIRT_R_OUT + FIT_SLIP          # skirt bore
LUG_SLOT_R = LUG_R_OUT + 0.25                   # bayonet slot / groove radius
CUP_R_OUT = LUG_SLOT_R + CUP_WALL               # outer radius of the cup
POCKET_R = BOARD_R + FIT_PCB                    # LED board pocket
BOARD_LEDGE_IN_R = COMPONENT_R_MAX + 0.2        # ledge under the board edge band (clear of bottom parts)
UNDER_BOARD_DEPTH = 2.2                         # room for bottom-side parts (TSSOP/0805 <= 1.3 mm) + wires
NUT_AF = 14.0                                   # M10x1 lamp-thread hex nut across flats (VERIFY with the gooseneck kit)
NUT_T = 3.0                                     # nut thickness (VERIFY)
NECK_THREAD_D = 10.0                            # gooseneck end thread (M10x1, VERIFY)
NECK_HOLE_R = NECK_THREAD_D / 2 + 0.25
FLOOR_T = 2.0

# ---- bayonet (shared by moon_shell lugs and moon_base grooves) ---------------------------------------
LUG_CHAMFER = 0.6          # 45 deg chamfer on the lug's top outer edge (prints upward-facing on the moon)
GROOVE_CLEAR = 0.25        # vertical / radial clearance of the lug in its groove
CAM_DROP = 0.35            # groove descends this much over the twist: pulls the moon down onto the LED board


def lug_profile(z0):
    """(r, z) polygon of a lug cross-section, z0 = lug bottom (skirt bottom)."""
    r0, r1, h, c = SKIRT_R_OUT - 0.3, LUG_R_OUT, LUG_H, LUG_CHAMFER
    return [(r0, z0), (r1, z0), (r1, z0 + h - c), (r1 - c, z0 + h), (r0, z0 + h)]


def groove_profile(z0):
    """(r, z) polygon of the groove cavity in the cup wall: the lug profile grown by GROOVE_CLEAR, with a 45 deg roof
    rising inward to the bore so the cavity prints without supports."""
    rin, rout = BORE_UPPER_R - 0.05, LUG_SLOT_R
    zb = z0 - 0.05
    zr = z0 + LUG_H - LUG_CHAMFER + GROOVE_CLEAR
    return [(rin, zb), (rout, zb), (rout, zr), (rin, zr + (rout - rin))]
