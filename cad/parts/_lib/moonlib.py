"""Shared dimensions for the moon, its LED base and the LED board (single source of truth, mm).

v0.2 head (LED board v0.2, 18 mm): the base cup sits INSIDE the moon's skirt (a slim stem instead of a wide cup
round the moon), the bayonet is turned inside out (lugs on the cup, grooves inside the moon's skirt) and the moon
clamps the PETG ring onto the board through a 45 deg cone. Everything is in "moon coordinates" (sphere centre at
z = 0) unless a name says otherwise; moon_base works in its own frame (bed at z = 0, see CUP_Z0).
"""
import math

# ---- moon --------------------------------------------------------------------------------------------
R_OUT = 25.0            # outer radius at the thickest lithophane point (50 mm moon)
T_MIN = 0.9             # thinnest lithophane wall (>= 0.84 hard minimum: 2 perimeters)
T_MAX = 2.6             # thickest lithophane wall
R_IN = R_OUT - T_MAX    # smooth inner sphere
COLLAR_K = R_OUT * math.sqrt(2)   # 45 deg outer collar (B8): r = COLLAR_K + z, tangent to the sphere at 45 deg

# ---- LED board v0.2 (hardware/led-board/design.py) -----------------------------------------------------
BOARD_R = 9.0           # 18 mm round, 1.0 mm FR4 (VERIFY with the order)
BOARD_T = 1.0
BOARD_CLAMP_IN = 8.0    # edge band r 8.0-9.0 is clamped (PETG ring above, cup ledge below): no copper/parts there
COMPONENT_R_MAX = 7.8   # all parts inside this radius on both faces
LED_RING_R = 5.8        # white 2835 centres (radial, long axis outward)
EMITTER_R_MAX = LED_RING_R + 1.3   # outer edge of a 2835's emitting area (lens ~2.6 mm along the radial axis)
EMITTER_H = 0.7         # emitting surface above the board top (2835 body 0.8 mm)
RGB_TOP_H = 1.9         # Wurth PLCC4 RGB body height (centre of the board)

# ---- optics (docs/design/optics.md, corrected model of 2026-11-03) ------------------------------------
OPEN_R = 9.0           # bottom opening on the inner sphere (half-angle ~23.7 deg): a 0.6 mm vertical bore under it
                        # meets the clamp cone, so the rim is a blunt lip, not a 67 deg knife edge (B14)
Z_CUT = -math.sqrt(R_IN ** 2 - OPEN_R ** 2)   # planar cut, sphere centre at z=0  (~ -20.81)
LED_DEPTH = 1.2         # white emitters below the opening plane: max/min ~1.05 on the visible wall (1.0 -> 1.03,
                        # 2.0 -> 1.12); the opening itself is the aperture, so deeper LEDs shade the low wall
BORE_R = OPEN_R         # straight bore under the opening: never narrower than the opening, so no LED ray that
                        # could pass the opening is clipped (no-shadow rule, moon_shell B14)

# ---- clamp stack --------------------------------------------------------------------------------------
Z_EMIT = Z_CUT - LED_DEPTH
Z_BOARD_TOP = Z_EMIT - EMITTER_H
Z_BOARD_BOT = Z_BOARD_TOP - BOARD_T
RING_T = 0.8            # PETG clamp ring on the board's edge band (thermal review: keeps PLA off the board);
                        # 4 layers, so the 45 deg chamfer leaves >= 0.55 mm of washer everywhere
RING_R_IN = BOARD_CLAMP_IN
RING_R_OUT = 9.9        # overhangs the cup's land (r 9.2-10.0) by design; it bears on the board, which stands
                        # 0.1 proud of the land (moon_base B11)
RING_CHAMFER = 0.4      # 45 deg on the ring's top outer edge: the moon's cone bears on it
Z_RING_TOP = Z_BOARD_TOP + RING_T
CONE_C = (RING_R_OUT - RING_CHAMFER) + Z_RING_TOP   # moon's 45 deg clamp cone: r + z = CONE_C
Z_BORE_BOT = min(CONE_C - BORE_R, Z_CUT)             # cone meets the bore (or reaches the cut plane first)
R_IN_EXACT = R_IN - 0.02                             # exact part's inner sphere below Z_TRIM: 0.02 inside the
                                                     # lithophane's, so its top face carries the trimmed lithophane
Z_BORE_TOP = -math.sqrt(R_IN_EXACT ** 2 - BORE_R ** 2)   # the bore meets the exact part's inner sphere here


def _ridge():
    """Where the clamp cone meets the inner sphere (the true opening rim): r = CONE_C - z on the sphere."""
    lo, hi = Z_CUT - 1.0, Z_CUT + 1.0                # sphere - cone changes sign between these
    f = lambda z: math.sqrt(R_IN_EXACT ** 2 - z * z) - (CONE_C - z)
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
    return (CONE_C - lo, lo)


R_RIDGE, Z_RIDGE = _ridge()                          # ~ (8.39, Z_CUT + 0.03): a 67 deg ridge, not a knife edge
Z_TRIM = Z_CUT + 0.3                                 # exact part steps into the lithophane wall here (band to Z_CUT + 0.6)
Z_ORG_TRIM = Z_TRIM - 0.1                            # lithophane trimmed 0.1 lower: its cut face lies inside the exact
                                                     # part (no coplanar faces); the exact part is 0.02 inside / 0.01
                                                     # outside the lithophane's surfaces below Z_TRIM

# ---- base cup (PETG) inside the moon's skirt, and the inverted bayonet --------------------------------
FIT_SLIP = 0.15         # radial slip fit printed part to printed part (VERIFY: fit coupon)
FIT_PCB = 0.2           # radial clearance PCB edge to printed bore
POCKET_R = BOARD_R + FIT_PCB                    # LED board pocket in the cup
CUP_WALL = 1.2
CUP_R = POCKET_R + CUP_WALL                     # cup outer radius (10.4)
GAP_45 = 0.25           # perpendicular clearance between facing 45 deg faces (cup top / moon cone, lug / groove)
TOP_C = CONE_C - GAP_45 * math.sqrt(2)          # cup rim bevel and lug tops: r + z = TOP_C
Z_LAND = Z_BOARD_TOP - 0.1                      # cup rim: flat land 0.1 under the board top (board proud, B11) ...
LAND_R_OUT = TOP_C - Z_LAND                     # ... out to the 45 deg bevel
LUG_N = 3
LUG_W = 3.0             # tangential width
LUG_R_OUT = CUP_R + 0.8
LUG_FACE_H = 0.5        # vertical outer face of a lug; top and bottom are 45 deg (prints without support)
Z_LUG_FACE_TOP = TOP_C - LUG_R_OUT
Z_LUG_FACE_BOT = Z_LUG_FACE_TOP - LUG_FACE_H
LUG_BOT_K = Z_LUG_FACE_BOT - LUG_R_OUT          # lug underside: z - r = LUG_BOT_K
LUG_ANGLES = tuple(90.37 + k * 360 / LUG_N for k in range(LUG_N))   # cup frame
BAYONET_TURN_DEG = 30.0
CAM_DROP = 0.25         # the groove floor rises this much over the turn: pulls the moon down onto the ring (VERIFY)
SKIRT_R_IN = CUP_R + FIT_SLIP
GROOVE_R = LUG_R_OUT + 0.25
SKIRT_WALL = 1.2
SKIRT_R_OUT = GROOVE_R + SKIRT_WALL             # 12.65 -> 25.3 mm skirt
FLOOR_K_LOCK = LUG_BOT_K                        # groove floor z - r at the end of the turn (bears on the lug)
FLOOR_K_OPEN = LUG_BOT_K - CAM_DROP - 0.1       # ... at the entry slot (0.1 free play before the cam bites)
Z_SKIRT_BOT = FLOOR_K_OPEN + SKIRT_R_IN - 1.2   # 1.2 mm of skirt below the lowest groove floor
Z_COLLAR_SKIRT = SKIRT_R_OUT - COLLAR_K         # the 45 deg collar meets the skirt's outer wall here

UNDER_BOARD_DEPTH = 4.5                         # nut top -> board underside: bottom parts (<= 1.45 mm) + the four
                                                # wires leaving the gooseneck bore and turning to the pads (R2-D3)
BOARD_LEDGE_IN_R = 8.35                         # ledge under the board's edge band: clear of the bottom parts (r 7.8)
                                                # and of the nut socket's corners (r 8.31), so the socket has no ceiling
NUT_AF = 14.0                                   # M10x1 lamp-thread hex nut across flats (VERIFY with the gooseneck kit)
NUT_T = 3.0                                     # nut thickness (VERIFY)
NECK_THREAD_D = 10.0                            # gooseneck end thread (M10x1, VERIFY)
NECK_HOLE_R = NECK_THREAD_D / 2 + 0.25
FLOOR_T = 2.0
Z_CUP0 = Z_BOARD_BOT - UNDER_BOARD_DEPTH - NUT_T - FLOOR_T   # moon-frame z of the cup's bed (cup z = moon z - Z_CUP0)


def opening_half_angle_deg():
    return math.degrees(math.asin(OPEN_R / R_IN))


def cup_z(z_moon):
    return z_moon - Z_CUP0


def emitter_cone_r(z):
    """Radius of the cone from the outermost emitter edge (EMITTER_R_MAX at Z_EMIT) to the opening rim (OPEN_R at
    Z_CUT): every LED ray that can pass the opening stays inside it (radial distance is convex along a ray)."""
    t = (z - Z_EMIT) / (Z_CUT - Z_EMIT)
    return EMITTER_R_MAX + (OPEN_R - EMITTER_R_MAX) * t


def lug_profile_cup():
    """(r, z) polygon of a lug cross-section on the cup's outer wall, in the CUP frame."""
    r0 = CUP_R - 0.3
    return [(r0, cup_z(TOP_C - r0)), (LUG_R_OUT, cup_z(Z_LUG_FACE_TOP)), (LUG_R_OUT, cup_z(Z_LUG_FACE_BOT)),
            (r0, cup_z(LUG_BOT_K + r0))]


def groove_profile(floor_k):
    """(r, z) polygon of the groove cavity in the moon's skirt (moon frame): roof = the clamp cone extended
    (45 deg, rising inward: prints as a 45 deg overhang), floor z - r = floor_k (rising outward), back wall GROOVE_R."""
    r0, c = SKIRT_R_IN - 0.05, CONE_C + 0.03     # roof 0.03 above the cone line: no face coincides with the cone
    return [(r0, floor_k + r0), (GROOVE_R, floor_k + GROOVE_R), (GROOVE_R, c - GROOVE_R), (r0, c - r0)]
