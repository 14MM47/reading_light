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
