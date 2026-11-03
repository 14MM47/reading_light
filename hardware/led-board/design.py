"""LED board v0.2 (in the moon's base), 18 mm round, 2 layers, 1.0 mm FR4, WHITE solder mask (reflector).

Top face (into the moon): 8 x CRI-97 white 2835 (4 x 2700 K, 4 x 5000 K) radial on a 5.8 mm ring, cathode pad
inward, and one Wurth RGB (common anode) at the centre. Bottom face: TI LP5012 12-channel constant-current driver
(WQFN-20, 3 x 3 mm) at the centre, NXP LM75B temperature sensor (its OS output holds the driver's EN low above
60 C: hardware thermostat), and 2 x 2 solder pads for the 4-wire cable up the neck.

Layout idea (docs/design/electronics.md, LED board v0.2): every LED cathode drops through a via onto a ring of
11 vias around the driver (r 2.9-3.6 mm). The bottom fan-in stays inside that ring, so the rest of the bottom
face is free for the sensor, the passives and the cable pads. The driver's control side (VCC, SDA, SCL, EN, IREF)
faces north into the one wide gap of the ring (the two north LEDs put their vias on the ring's bisectors).

Optics (docs/design/optics.md): LED plane below the moon's bottom opening, with a 30 degree flared skirt bore so
the opening never shadows the low-angle light. The edge band r 8.0-9.0 mm is clamped by the moon ring: no copper
or parts there (edge clearance 1.0 mm).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

HW = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HW / "tools"))
sys.path.insert(0, str(HW))
from kigen.schematic import Part  # noqa: E402
from parts import CAT  # noqa: E402

PROJECT = "led-board"
TITLE = "Moon reading light - LED board (moon base)"
REV = "0.2"
DATE = "2026-11-03"
PAPER = "A3"
CX, CY, R_BOARD = 50.0, 50.0, 9.0
RING_R = 5.8              # white LED centres; 2835 bodies reach r 7.68 (inside the r 7.8 part limit)
PART_R_MAX = 7.8          # bodies and pads stay inside this radius (moon_base ledge / moon ring clamp at r 8-9)

LIB = {"LEDDRV": "reading_light:LP5012RUK", "TEMP": "Sensor_Temperature:MCP9800Ax-xOT", "LED_WW": "Device:LED",
       "LED_CW": "Device:LED", "LED_RGB": "Device:LED_ABRG", "R_2K94_0402": "Device:R", "R_2K4_0402": "Device:R",
       "C_100N_0402": "Device:C", "C_10U_0603": "Device:C", "C_1U_0402": "Device:C"}


def P(ref, cat, pins, sch, value=None, footprint=None, **kw):
    c = CAT[cat]
    fields = {"MPN": c.mpn, "Manufacturer": c.mfr, "Farnell": c.farnell, "Datasheet": c.datasheet,
              "Description": c.desc}
    return Part(ref, LIB[cat], value or c.value, footprint or c.footprint, pins, sch=sch, fields=fields, **kw)


# ---------------------------------------------------------------------------------------------- LEDs and vias
WHITE = [  # ref, group, angle (deg, 0 = +x, counter-clockwise seen from the TOP face)
    ("D1", "WW", 22.5), ("D2", "CW", 67.5), ("D3", "WW", 112.5), ("D4", "CW", 157.5),
    ("D5", "WW", 202.5), ("D6", "CW", 247.5), ("D7", "WW", 292.5), ("D8", "CW", 337.5),
]
RGB_REF, RGB_ROT = "D9", 90          # RGB at the centre; rot 90: anode NW, blue NE, red SW, green SE (top view)
GROUP_ID = {"WW": 0, "CW": 1, "R": 2, "G": 3, "B": 4}
N_OUT = 12
PIN_OF_OUT = {k: str(2 + k) for k in range(N_OUT)}      # LP5012 RUK: OUT0..OUT11 = pins 2..13
VIA_R = 3.25              # cathode via radius on the LED centreline (0.25 mm inside the cathode pad, r 3.8)
BISECT_R = 3.6            # the two north LEDs put their via on the ring bisector instead (opens the control gap)
NORTH = {"D2": 45.0, "D3": 135.0}


def _polar(r, ang):
    a = math.radians(ang)
    return (round(CX + r * math.cos(a), 3), round(CY - r * math.sin(a), 3))   # KiCad y points down


def cathode_vias():
    """{cathode net: (x, y)} for every LED cathode via (top pad -> bottom fan-in ring)."""
    v = {}
    for ref, _grp, ang in WHITE:
        v[f"K_{ref}"] = _polar(BISECT_R, NORTH[ref]) if ref in NORTH else _polar(VIA_R, ang)
    v[f"K_{RGB_REF}_B"] = (CX + 3.0, CY + 0.15)        # east, between the D1 and D8 vias
    v[f"K_{RGB_REF}_G"] = (CX + 0.42, CY + 2.95)       # south, below the green pad
    v[f"K_{RGB_REF}_R"] = (CX - 0.42, CY + 2.95)       # south, below the red pad
    return v


def _pad_xy(fpid, x, y, rot, side, pad_number):
    import pcbnew
    lib, name = fpid.split(":")
    libdir = str(HW / "lib" / "reading_light.pretty") if lib == "reading_light" else \
        f"/usr/share/kicad/footprints/{lib}.pretty"
    global _TMP_BOARD
    _TMP_BOARD = pcbnew.BOARD()          # footprints must live on a board before Flip()
    fp = pcbnew.FootprintLoad(libdir, name)
    _TMP_BOARD.Add(fp)
    fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    if side == "B":
        fp.Flip(pcbnew.VECTOR2I_MM(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(rot)
    for p in fp.Pads():
        if p.GetNumber() == pad_number:
            return pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)
    raise KeyError(pad_number)


def _bearing_cw_from_north_gap(x, y):
    """Clockwise angle (deg, as seen from the top) from the middle of the north gap. Used for both the vias and
    the driver pins, so sorting by it gives the planar fan-in order."""
    a = math.degrees(math.atan2(-(y - CY), x - CX))          # counter-clockwise from +x
    return (90.0 - a) % 360.0


def assign_outputs():
    """{cathode net: LP5012 output}. The vias and the output pins are both taken in clockwise order around the
    driver; the vias are mapped onto the pins in that order (a planar fan-in: no track crosses another), skipping
    the one spare output where it shortens the tracks most."""
    vias = cathode_vias()
    order = sorted(vias, key=lambda n: _bearing_cw_from_north_gap(*vias[n]))
    ux, uy, urot, uside = PLACE["U1"]
    pins = [_pad_xy(CAT["LEDDRV"].footprint, ux, uy, urot, uside, PIN_OF_OUT[o]) for o in range(N_OUT)]
    pin_order = sorted(range(N_OUT), key=lambda o: _bearing_cw_from_north_gap(*pins[o]))
    best = None
    for skip in range(N_OUT):
        outs = [o for o in pin_order if o != pin_order[skip]]
        cost = sum(math.dist(vias[n], pins[o]) for n, o in zip(order, outs))
        if best is None or cost < best[0]:
            best = (cost, dict(zip(order, outs)))
    return best[1]


def out_group():
    g = [-1] * N_OUT
    for net, o in assign_outputs().items():
        if net.endswith(("_R", "_G", "_B")):
            g[o] = GROUP_ID[net[-1]]
        else:
            ref = net[2:]
            g[o] = GROUP_ID[next(w[1] for w in WHITE if w[0] == ref)]
    return g


# ---------------------------------------------------------------------------------------------- schematic
def parts():
    v = []
    amap = assign_outputs()
    outs = {o: None for o in range(N_OUT)}
    for net, o in amap.items():
        outs[o] = net
    for i, (ref, grp, ang) in enumerate(WHITE):
        v.append(P(ref, "LED_WW" if grp == "WW" else "LED_CW", {"1": f"K_{ref}", "2": "VLED"},
                   (40 + 22 * i, 50, 270), value=("2700K" if grp == "WW" else "5000K") + " CRI97"))
    v.append(P(RGB_REF, "LED_RGB", {"1": "VLED", "2": f"K_{RGB_REF}_B", "3": f"K_{RGB_REF}_R",
                                     "4": f"K_{RGB_REF}_G"}, (230, 50, 0)))
    drv = {"16": "VLED", "17": "SDA", "18": "SCL", "19": "EN", "20": "IREF", "1": "VCAP",
           "14": "GND", "15": "GND", "21": "GND"}               # ADDR1 = ADDR0 = GND -> I2C address 0x14
    for o, pin in PIN_OF_OUT.items():
        drv[pin] = outs[o]                                       # None = unused output (may float)
    v += [
        P("U1", "LEDDRV", drv, (95, 160, 0), value="LP5012"),
        P("R1", "R_2K94_0402", {"1": "IREF", "2": "GND"}, (50, 180, 0), value="2.94k (25 mA)"),
        P("C1", "C_1U_0402", {"1": "VLED", "2": "GND"}, (40, 150, 0)),      # VCC bypass
        P("C4", "C_1U_0402", {"1": "VCAP", "2": "GND"}, (60, 180, 0)),      # internal LDO cap, at pin 1
        P("C2", "C_10U_0603", {"1": "VLED", "2": "GND"}, (28, 150, 0)),     # bulk at the LEDs (end of the cable)
        # hardware thermostat: MCP9800 ALERT (open drain, active low, comparator mode; firmware sets TSET 60 C /
        # THYST 52 C) pulls the LP5012 EN low (shutdown, all outputs off) even if the MCU or the bus has failed.
        P("U2", "TEMP", {"1": "VLED", "2": "GND", "3": "EN", "4": "SCL", "5": "SDA"}, (190, 160, 0),
          value="MCP9800A0"),
        # 2.4 k: a stiff EN node next to the metal neck (round2 R2-E5). ALERT sinks <= 1.75 mA while asserted.
        P("R2", "R_2K4_0402", {"1": "VLED", "2": "EN"}, (150, 145, 0)),
        P("C3", "C_100N_0402", {"1": "VLED", "2": "GND"}, (215, 145, 0)),
        # J1 pin numbers are arbitrary (solder pads): 1 GND, 2 VLED, 3 SCL, 4 SDA; the wires go by the G V C D silk
        Part("J1", "Connector_Generic:Conn_02x02_Odd_Even", "MOON CABLE", "reading_light:LED_WirePads_2x02_P1.90mm",
             {"1": "GND", "2": "VLED", "3": "SCL", "4": "SDA"}, sch=(270, 160, 180),
             fields={"Description": "2x2 solder pads for the 4-wire cable (Qwiic colours: black GND, red VLED, "
                                    "blue SDA, yellow SCL; silk G V D C)", "MPN": "-", "Farnell": ""}, in_bom=False),
    ]
    return v


PWR_FLAGS = [("VLED", (300, 130)), ("GND", (310, 130))]
NOTES = [("LEDs - top face (into the moon)", (22, 30)), ("Driver, sensor, cable - bottom face", (22, 120))]
BOXES = [(20, 25, 400, 95), (20, 115, 400, 210)]
COMMENTS = [
    "LP5012 RIREF 2.94k -> 105 x 0.7 V / 2.94 k = 25.0 mA per output (Wurth RGB abs max 30 mA). All anodes on VLED.",
    "I2C: LP5012 0x14 (ADDR1 = ADDR0 = GND), LM75B 0x48. Pull-ups on the main board. EN <- LM75B OS (thermostat).",
    "Top face white mask (reflector). Edge band r 8-9 mm is clamped by the moon ring: no copper there.",
]

# ============================================================================================== PCB


def _circle(r, n=72):
    return [(round(CX + r * math.cos(2 * math.pi * k / n), 4), round(CY + r * math.sin(2 * math.pi * k / n), 4))
            for k in range(n)]


OUTLINE = ("circle", CX, CY, R_BOARD)
BOARD_THICKNESS = 1.0   # mm: keeps the LED plane low in the moon base (optics stack, FAB_NOTES)
RULES = {"clearance": 0.15, "track": 0.15, "track_min": 0.15, "via": 0.6, "drill": 0.3, "edge_clear": 1.0,
         "annular_min": 0.125, "hole_to_hole": 0.5}
NETCLASSES = [dict(name="Power", track=0.3, clearance=0.15, via=0.6, drill=0.3, nets=["VLED"])]
ROUTE_GRID = 0.05
ROUTE_ALIGN = (CX, CY)       # LP5012 pad centre lines (0.4 mm pitch about the centre) fall on router cell centres
ROUTE_OPTS = {"layer_cost": (4.0, 1.0), "via_cost_mm": 2.0}   # keep the LED face (VLED pour) intact


def _place():
    p = {}
    for ref, grp, ang in WHITE:
        # radial: footprint +x (pad 1 cathode -> pad 2 anode) points outward, so the cathode pad is inward
        p[ref] = (*_polar(RING_R, ang), round(ang, 2), "F")
    p[RGB_REF] = (CX, CY, RGB_ROT, "F")
    p.update({
        "U1": (CX, CY, 180, "B"),                 # LP5012: control pins 16-20 face north, VCAP NE, ADDR NW
        "R1": (CX + 1.75, CY - 4.4, 0, "B"),      # RIREF, north-east of pin 20 (IREF on pad 1, west)
        "C4": (CX + 3.5, CY - 3.15, 270, "B"),    # VCAP cap, north-east of pin 1 (VCAP on pad 1, north)
        "C1": (CX - 2.7, CY - 4.4, 0, "B"),       # VCC bypass, north-west of the VCC via
        "U2": (CX + 5.7, CY + 0.0, 0, "B"),       # MCP9800, east: ALERT NW, SCL NE, SDA SE, VDD SW, GND W
        "C3": (CX + 4.4, CY + 2.75, 270, "B"),    # MCP9800 bypass, below its VDD pin (VLED pad 1 north)
        # EN pull-up on the TOP face, tangential in the outer NE gap between D1 and D2 (r 7.25): the bottom
        # face has no room left inside the I2C/EN arc. 0402, 0.35 mm tall, well clear of the LED light paths.
        "R2": (*_polar(7.25, 45.0), 135, "F"),
        "J1": (CX + 0.0, CY + 6.05, 270, "B"),    # cable pads, south: NW GND, SW VLED, NE SCL, SE SDA
        "C2": (CX - 5.6, CY + 0.0, 90, "B"),      # bulk 10 uF, west
    })
    return p


PLACE = _place()


def _arc(r, a0, a1, step=4.0):
    """Points on the circle of radius r about the board centre from bearing a0 to a1 (deg, either direction)."""
    n = max(1, int(abs(a1 - a0) / step))
    return [_polar(r, a0 + (a1 - a0) * k / n) for k in range(n + 1)]


EN_VIA = _polar(6.4, 45.0)       # EN drops to the top face here, for the pull-up R2 in the NE gap between D1/D2


def bundle_tracks(w=0.15):
    """Fixed copper for the I2C/EN bundle and the sensor's local nets (the greedy router cannot find this
    topology). From the LP5012 north side the three nets run up and clockwise as concentric arcs, EN inside
    (r 6.4), SCL (r 7.0), SDA outside (r 7.45), down to the MCP9800 on the east: EN to ALERT (NW), SCL to its
    NE pin and on under the sensor body, SDA round the sensor's east side to its SE pin. SCL and SDA then carry on
    clockwise (r 7.0 / r 7.7) to the cable pads in the south. Everything else (IREF, VCAP and the passives
    inside the arc) stays inside the arcs, so GND reaches it through the gap north of the cable pads."""
    ux, uy, urot, uside = PLACE["U1"]
    fp = CAT["LEDDRV"].footprint
    pin = {n: _pad_xy(fp, ux, uy, urot, uside, n) for n in ("17", "18", "19")}
    sx, sy, srot, sside = PLACE["U2"]
    sp = {n: _pad_xy(CAT["TEMP"].footprint, sx, sy, srot, sside, n) for n in "12345"}
    jx, jy, jrot, jside = PLACE["J1"]
    jp = {n: _pad_xy("reading_light:LED_WirePads_2x02_P1.90mm", jx, jy, jrot, jside, n) for n in "34"}
    cx3, cy3, crot3, cside3 = PLACE["C3"]
    c3 = {n: _pad_xy(CAT["C_100N_0402"].footprint, cx3, cy3, crot3, cside3, n) for n in "12"}
    rx, ry, rrot, rside = PLACE["R2"]
    r2en = _pad_xy(CAT["R_2K4_0402"].footprint, rx, ry, rrot, rside, "2")
    east_x = sp["5"][0] + 0.663 + 0.23            # SDA down the sensor's east side (pad tip + 0.23)
    t = []

    def T(net, pts, layer="B", width=w):
        t.append(dict(pts=[(round(x, 3), round(y, 3)) for x, y in pts], width=width, layer=layer, net=net))

    # EN: north, arc r 6.4, down to ALERT (pin 3) from the north
    en_top = (pin["19"][0], CY - math.sqrt(6.4 ** 2 - (pin["19"][0] - CX) ** 2))
    a_en = math.degrees(math.atan2(CY - en_top[1], en_top[0] - CX))
    T("EN", [pin["19"], en_top] + _arc(6.4, a_en, 34.0)[1:] + [(sp["3"][0] + 0.14, sp["3"][1] - 0.5), sp["3"]])
    T("EN", [EN_VIA, r2en], layer="F", width=0.2)
    # SCL: north, arc r 7.0, into pin 4 from the north, through the pad to its inner end, under the body, out south
    scl_top = (pin["18"][0], CY - math.sqrt(7.0 ** 2 - (pin["18"][0] - CX) ** 2))
    a_scl = math.degrees(math.atan2(CY - scl_top[1], scl_top[0] - CX))
    inner4 = (sp["4"][0] - 0.66, sp["4"][1])
    T("SCL", [pin["18"], scl_top] + _arc(7.0, a_scl, 26.0)[1:] + [(sp["4"][0] - 0.09, sp["4"][1] - 0.5), sp["4"],
             inner4, (sx, sp["4"][1] + 0.4), (sx, sp["5"][1] + 0.6)] + _arc(7.0, -24.5, -63.0) +
      [(jp["3"][0] + 0.6, jp["3"][1]), jp["3"]])
    # SDA: north, arc r 7.45, down the east side, into pin 5 from the east, then on clockwise at r 7.7 to J1
    sda_top = (pin["17"][0], CY - math.sqrt(7.45 ** 2 - (pin["17"][0] - CX) ** 2))
    a_sda = math.degrees(math.atan2(CY - sda_top[1], sda_top[0] - CX))
    T("SDA", [pin["17"], sda_top] + _arc(7.45, a_sda, 14.0)[1:] + [(east_x, sp["4"][1] - 0.5), (east_x, sp["5"][1]),
             sp["5"]])
    T("SDA", [(east_x, sp["5"][1])] + _arc(7.7, -10.5, -72.0) + [(jp["4"][0] + 0.6, jp["4"][1]), jp["4"]])
    # sensor VDD (pin 1, SW) -> C3 -> a VLED via in the SE gap between D7 and D8; GND (pin 2, W) down the west side
    T("VLED", [sp["1"], (sp["1"][0], sp["1"][1] + 0.5), c3["1"], (c3["1"][0] + 0.65, c3["1"][1] + 0.03),
               (c3["1"][0] + 0.75, c3["1"][1] + 1.43), SENSOR_VDD_VIA], width=0.2)
    T("GND", [sp["2"], (sp["2"][0] - 0.94, sp["2"][1]), (sp["2"][0] - 0.94, c3["2"][1]), c3["2"]])
    return t


SENSOR_VDD_VIA = (CX + 4.9, CY + 4.0)


def _seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1e-12)))
    return math.hypot(ax + t * dx - px, ay + t * dy - py)


# stub length (mm past the pad centre) per cathode net where the default 0.55 would bring two legs too close:
# a pin whose leg turns less sharply goes further out before turning (found with _check_fanin)
STUB = {"K_D2": 0.5, "K_D1": 0.65, "K_D4": 0.75}


def fanin_tracks(width=0.15, stub=None):
    """Fixed copper for every LED cathode: a radial top track from the cathode pad to its via, and on the bottom a
    straight stub out of the LP5012 pin (0.55 mm, perpendicular to the package side) then one straight leg to the
    via. The legs follow the planar order of assign_outputs(), so they never cross; _check_fanin() verifies it."""
    vias = cathode_vias()
    ux, uy, urot, uside = PLACE["U1"]
    t = []
    for net, o in assign_outputs().items():
        px, py = _pad_xy(CAT["LEDDRV"].footprint, ux, uy, urot, uside, PIN_OF_OUT[o])
        dx, dy = px - ux, py - uy
        ox, oy = (math.copysign(1, dx), 0.0) if abs(dx) > abs(dy) else (0.0, math.copysign(1, dy))
        L = (stub or STUB).get(net, 0.55)
        end = (round(px + ox * L, 3), round(py + oy * L, 3))
        t.append(dict(pts=[(px, py), end, vias[net]], width=width, layer="B", net=net))
    for ref, _grp, ang in WHITE:          # top: cathode pad (inner edge, r 3.8) -> via
        vx, vy = vias[f"K_{ref}"]
        a = math.radians(ang)
        if ref in NORTH:                  # the via sits on the bisector: leave the pad from its inner corner
            b = math.radians(NORTH[ref])
            side = math.copysign(1.0, math.sin(b - a))
            u, v = 4.0, side * 0.8        # a point inside the pad, near the corner facing the via
            start = (CX + u * math.cos(a) - v * math.sin(a), CY - (u * math.sin(a) + v * math.cos(a)))
        else:
            start = _polar(4.2, ang)
        t.append(dict(pts=[(round(start[0], 3), round(start[1], 3)), (vx, vy)], width=0.25, layer="F", net=f"K_{ref}"))
    rx, ry, _r, _s = PLACE[RGB_REF]
    for c, pad in (("B", "2"), ("R", "3"), ("G", "4")):
        px, py = _pad_xy(CAT["LED_RGB"].footprint, rx, ry, RGB_ROT, "F", pad)
        t.append(dict(pts=[(round(px, 3), round(py, 3)), vias[f"K_{RGB_REF}_{c}"]], width=0.2, layer="F",
                      net=f"K_{RGB_REF}_{c}"))
    return t


def _check_fanin(tracks, min_gap=0.15):
    """Centre-line clearance between bottom fan-in legs of different nets, from each leg to other nets' vias, and
    to the LP5012's VCAP pin (pin 1, next to OUT0)."""
    segs = [(tr["net"], a, b, tr["width"]) for tr in tracks if tr["layer"] == "B" for a, b in zip(tr["pts"], tr["pts"][1:])]
    ux, uy, urot, uside = PLACE["U1"]
    p1 = _pad_xy(CAT["LEDDRV"].footprint, ux, uy, urot, uside, "1")
    segs.append(("VCAP", (p1[0] - 0.25, p1[1]), (p1[0] + 0.25, p1[1]), 0.2))
    worst = []
    for i, (n1, a1, b1, w1) in enumerate(segs):
        for n2, a2, b2, w2 in segs[i + 1:]:
            if n1 == n2:
                continue
            dmin = min(_seg_dist(a1, a2, b2), _seg_dist(b1, a2, b2), _seg_dist(a2, a1, b1), _seg_dist(b2, a1, b1))
            worst.append((dmin - (w1 + w2) / 2, n1, n2))
        for n2, (vx, vy) in cathode_vias().items():
            if n2 != n1:
                worst.append((_seg_dist((vx, vy), a1, b1) - 0.3 - w1 / 2, n1, n2 + " via"))
    worst.sort()
    return [w for w in worst if w[0] < min_gap]
# the cathode vias are placed by the design (cathode_vias), so the fan-in is planar; the router joins them
VIAS = [dict(x=x, y=y, net=n) for n, (x, y) in cathode_vias().items()] + \
       [dict(x=CX - 1.0, y=CY - 2.85, net="VLED"),          # LP5012 VCC (pin 16) up to the top pour
        dict(x=EN_VIA[0], y=EN_VIA[1], net="EN"),           # EN to the top-face pull-up R2
        dict(x=SENSOR_VDD_VIA[0], y=SENSOR_VDD_VIA[1], net="VLED")]
TRACKS = [dict(pts=[(CX - 0.8, CY - 1.4), (CX - 0.8, CY - 2.2), (CX - 1.0, CY - 2.85)], width=0.25, layer="B",
               net="VLED")] + fanin_tracks() + [
    # exposed pad (GND) <- ADDR1/ADDR0 pins 15/14 (the only way into the EP: 0.2 mm links between 0.4 mm-pitch pads)
    dict(pts=[(CX - 1.4, CY - 0.8), (CX - 0.6, CY - 0.8)], width=0.2, layer="B", net="GND"),
    dict(pts=[(CX - 1.4, CY - 0.4), (CX - 0.6, CY - 0.4)], width=0.2, layer="B", net="GND"),
    # ... and out of pin 15 to the north, between the NNW cathode leg and the VCC via, into the GND pour
    dict(pts=[(CX - 1.5, CY - 0.8), (CX - 1.75, CY - 1.05), (CX - 1.75, CY - 3.4)], width=0.3, layer="B", net="GND"),
] + bundle_tracks()
# (the LED cathodes are pre-routed: fanin_tracks). 0.15 mm for every net that leaves an LP5012 pin: its pads are 0.2 mm wide on a 0.4 mm pitch, and the router's
# clearance margin does not let a 0.2 mm track out of a middle pin (0.15 / 0.15 mm is a standard fab rule)
ROUTE = [("IREF", 0.15), ("VCAP", 0.15),
         ("GND", 0.3, {"layers": (1,), "optional": True}),   # the bottom pour finishes GND (DRC checks it)
         ("VLED", 0.3, {"layers": (0,)})]   # top-only tree joining every anode and the pre-stitched vias
PRE_STITCH = [("VLED", 1)]   # every bottom-side VLED pad gets a via to the top VLED pour before routing
STITCH_SKIP_CONNECTED = True # ... unless it already has one (the LP5012 VCC pin's pre-placed via)
STITCH = []
STITCH_GRID = []
ZONES = [dict(net="GND", layer="B", pts=_circle(R_BOARD - 0.2), clearance=0.2, min_width=0.2),
         dict(net="VLED", layer="F", pts=_circle(R_BOARD - 0.2), clearance=0.2, min_width=0.2)]
def _silk():
    t = []
    # top: W = 2700 K, C = 5000 K in the gap on each white LED's counter-clockwise side (round2 R2-D10); D1's
    # goes on its clockwise side because R2 sits in its counter-clockwise gap
    for ref, grp, ang in WHITE:
        b = ang - 17.0 if ref == "D1" else ang + 17.0
        x, y = _polar(6.8, b)
        t.append(dict(s="W" if grp == "WW" else "C", x=x, y=y, size=0.8, thick=0.13, layer="F.SilkS"))
    # bottom: cable pad letters beside J1 (G V on the west pads, C D on the east pads), board name/rev/date
    jx, jy = PLACE["J1"][:2]
    for letter, dx, dy in (("G", -2.4, -0.95), ("V", -2.4, 0.95), ("C", 2.4, -0.95), ("D", 2.4, 0.95)):
        t.append(dict(s=letter, x=jx + dx, y=jy + dy, size=0.8, thick=0.13, layer="B.SilkS"))
    t += [dict(s="LED v0.2", x=CX - 4.35, y=CY + 2.55, size=0.8, thick=0.13, layer="B.SilkS"),
          dict(s="2026-11", x=CX - 4.35, y=CY + 3.65, size=0.8, thick=0.13, layer="B.SilkS")]
    return t


SILK = _silk()
SILK_R_MAX = 7.9             # silk stays inside the part-free radius (the r 8-9 band is clamped by the moon ring)
PAD_MAP = {}

FAB_NOTES = """# led-board v0.2 - fabrication notes (paste into the fab's order form)

- 2 layers, FR4, **1.0 mm**, 1 oz outer copper, round **18.0 mm** diameter
- Surface finish: **ENIG** (flat pads for the 2835 LEDs and the 0.4 mm pitch WQFN)
- Solder mask **WHITE** both sides (the top face is the reflector inside the moon), silkscreen black
- Min track / space **0.15 / 0.15 mm**; vias 0.6 / 0.3 mm (drill), min hole 0.3 mm; no blind/buried vias;
  vias tented both sides
- Quantity 5. Stencils: top 0.12 mm (LEDs) and bottom **0.10 mm** (LP5012 WQFN-20, 0.4 mm pitch); frameless
- Small round board: please leave no breakaway-tab nubs on the edge (it sits in an 18.4 mm pocket), or we sand them
- Silk: "W" = 2700 K and "C" = 5000 K beside each white LED; RGB D9: the package's polarity mark (pin 3, red
  cathode) goes on the silk chamfer; cable pads G V D C on the bottom
- Assembly (optional): TOP: D1-D9 and R2 (0402); BOTTOM: U1 LP5012 (WQFN-20), U2 MCP9800 (SOT-23-5), R1, C1-C4.
  J1 = 4 solder pads for the cable (not a component). Two-sided assembly costs extra; or assemble the bottom
  only and hand-fit the top.
"""
