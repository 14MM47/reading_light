"""LED board (in the moon's base): 8 x CRI-97 white 2835 (4 x 2700K, 4 x 5000K) + 2 x RGB on the top face,
TLC59116 16-ch constant-current driver + LM75B temperature sensor on the bottom face, 4 wire pads (GND, VLED,
SDA, SCL) for the cable up the neck. 26 mm round, 2 layers, 1.0 mm FR4, WHITE solder mask (reflector).

Optics (docs/design/optics): LEDs face into the moon from its bottom opening; the LED plane sits 1.8 mm below the
opening plane, which gives near-uniform wall illuminance (Lambertian source on the sphere wall). Board edge band
r 12.0-13.0 mm is clamped by the moon's skirt: no copper or parts there (edge clearance 1.0 mm).
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
REV = "0.1"
PAPER = "A3"
CX, CY, R_BOARD = 50.0, 50.0, 13.0
RING_R = 8.0

LIB = {"LEDDRV": "reading_light:TLC59116IPW", "TEMP": "reading_light:LM75BDP", "LED_WW": "Device:LED",
       "LED_CW": "Device:LED", "LED_RGB": "Device:LED_ABRG", "R_750": "Device:R", "R_10K": "Device:R", "R_2K4": "Device:R",
       "C_100N": "Device:C", "C_10U": "Device:C", "C_1U": "Device:C"}


def P(ref, cat, pins, sch, value=None, footprint=None, **kw):
    c = CAT[cat]
    fields = {"MPN": c.mpn, "Manufacturer": c.mfr, "Farnell": c.farnell, "Datasheet": c.datasheet,
              "Description": c.desc}
    return Part(ref, LIB[cat], value or c.value, footprint or c.footprint, pins, sch=sch, fields=fields, **kw)


# LED groups. Which TLC59116 output drives which cathode is solved geometrically (assign_outputs) so the
# cathode tracks fan in without crossing; firmware/include/board_map.h is generated from the result.
WHITE = [  # ref, group, angle (deg, 0 = +x, counter-clockwise seen from the TOP face)
    ("D1", "WW", 22.5), ("D2", "CW", 67.5), ("D3", "WW", 112.5), ("D4", "CW", 157.5),
    ("D5", "WW", 202.5), ("D6", "CW", 247.5), ("D7", "WW", 292.5), ("D8", "CW", 337.5),
]
RGB = [("D9", -3.0), ("D10", 3.0)]   # ref, x offset from the centre (top face)
GROUP_ID = {"WW": 0, "CW": 1, "R": 2, "G": 3, "B": 4}
PIN_OF_OUT = {0: "6", 1: "7", 2: "8", 3: "9", 4: "11", 5: "12", 6: "13", 7: "14", 8: "15", 9: "16", 10: "17",
              11: "18", 12: "20", 13: "21", 14: "22", 15: "23"}


def _pad_xy(fpid, x, y, rot, side, pad_number):
    import pcbnew
    lib, name = fpid.split(":")
    global _TMP_BOARD
    _TMP_BOARD = pcbnew.BOARD()          # footprints must live on a board before Flip()
    fp = pcbnew.FootprintLoad(f"/usr/share/kicad/footprints/{lib}.pretty", name)
    _TMP_BOARD.Add(fp)
    fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    if side == "B":
        fp.Flip(pcbnew.VECTOR2I_MM(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(rot)
    for p in fp.Pads():
        if p.GetNumber() == pad_number:
            return pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)
    raise KeyError(pad_number)


def assign_outputs():
    """{cathode net: TLC output} minimising the angular mismatch between each LED and its output pin."""
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    cath = []
    for ref, grp, ang in WHITE:
        cath.append((f"K_{ref}", math.radians(ang)))
    for ref, dx in RGB:
        a = math.atan2(0.0, dx)
        for c in "RGB":
            cath.append((f"K_{ref}_{c}", a))
    ux, uy, urot, uside = PLACE["U1"]
    pins = []
    for o in range(16):
        px, py = _pad_xy(CAT["LEDDRV"].footprint, ux, uy, urot, uside, PIN_OF_OUT[o])
        pins.append(math.atan2(-(py - CY), px - CX))
    cost = np.zeros((len(cath), 16))
    for i, (_, a) in enumerate(cath):
        for o, b in enumerate(pins):
            d = abs((a - b + math.pi) % (2 * math.pi) - math.pi)
            cost[i, o] = d * d
    rows, cols = linear_sum_assignment(cost)
    return {cath[i][0]: int(o) for i, o in zip(rows, cols)}


def out_group():
    g = [-1] * 16
    for net, o in assign_outputs().items():
        if net.endswith(("_R", "_G", "_B")):
            g[o] = GROUP_ID[net[-1]]
        else:
            ref = net[2:]
            g[o] = GROUP_ID[next(w[1] for w in WHITE if w[0] == ref)]
    return g


def parts():
    v = []
    amap = assign_outputs()
    outs = {o: None for o in range(16)}
    for net, o in amap.items():
        outs[o] = net
    # LEDs (sheet top)
    for i, (ref, grp, ang) in enumerate(WHITE):
        v.append(P(ref, "LED_WW" if grp == "WW" else "LED_CW", {"1": f"K_{ref}", "2": "VLED"},
                   (40 + 22 * i, 50, 270), value=("2700K" if grp == "WW" else "5000K") + " CRI97"))
    for j, (ref, dx) in enumerate(RGB):
        v.append(P(ref, "LED_RGB", {"1": "VLED", "2": f"K_{ref}_B", "3": f"K_{ref}_R", "4": f"K_{ref}_G"},
                   (230 + 40 * j, 50, 0)))
    pin_of_out = PIN_OF_OUT
    tlc = {"28": "VLED", "27": "SDA", "26": "SCL", "25": "RESET_N", "1": "REXT", "2": "GND", "3": "GND", "4": "GND",
           "5": "GND", "10": "GND", "19": "GND", "24": "GND"}
    for o, pin in pin_of_out.items():
        tlc[pin] = outs[o]
    v += [
        P("U1", "LEDDRV", tlc, (90, 160, 0)),
        P("R1", "R_750", {"1": "REXT", "2": "GND"}, (55, 175, 0), value="750 (25 mA)"),
        P("C1", "C_100N", {"1": "VLED", "2": "GND"}, (35, 145, 0)),
        P("C2", "C_10U", {"1": "VLED", "2": "GND"}, (25, 145, 0)),
        # hardware thermostat: LM75B OS (open-drain, active low; firmware sets Tos 60 C / Thyst 52 C) holds the
        # TLC59116 in reset, so the LEDs go dark even if the MCU or the I2C bus has failed (review M-1)
        P("U2", "TEMP", {"8": "VLED", "4": "GND", "1": "SDA", "2": "SCL", "3": "RESET_N", "5": "GND", "6": "GND",
                         "7": "GND"}, (190, 160, 0), value="LM75BDP"),
        # 2.4 k, not 10 k: a stiffer RESET_N node near the metal neck (round2 R2-E5; a filter cap did not route on
        # this 26 mm board). OS sinks 1.75 mA only while asserted (> 60 C): ~0.7 mW, negligible self-heating
        P("R2", "R_2K4", {"1": "VLED", "2": "RESET_N"}, (45, 145, 0)),
        P("C3", "C_100N", {"1": "VLED", "2": "GND"}, (210, 145, 0)),
        Part("J1", "Connector_Generic:Conn_01x04", "MOON CABLE", "reading_light:LED_WirePads_1x04_P2.00mm",
             {"1": "GND", "2": "VLED", "3": "SDA", "4": "SCL"}, sch=(270, 160, 180),
             fields={"Description": "Solder pads for the 4-wire cable (Qwiic colours: 1 black GND, 2 red VLED, "
                                    "3 blue SDA, 4 yellow SCL)", "MPN": "-", "Farnell": ""}, in_bom=False),
    ]
    return v


PWR_FLAGS = [("VLED", (300, 130)), ("GND", (310, 130))]
NOTES = [("LEDs - top face (into the moon)", (22, 30)), ("Driver, sensor, cable - bottom face", (22, 120))]
BOXES = [(20, 25, 400, 95), (20, 115, 400, 210)]
COMMENTS = [
    "TLC59116 REXT 750R -> 25.0 mA per output (Wurth RGB abs max 30 mA). All LED anodes on VLED. RESET <- LM75B OS (thermostat).",
    "I2C: TLC59116 0x60 (A3..A0 = GND), LM75B 0x48. Pull-ups are on the main board.",
    "Top face white mask (reflector). Edge band r 12-13 mm is clamped by the moon skirt: no copper there.",
]

# ============================================================================ PCB


def _circle(r, n=72):
    return [(round(CX + r * math.cos(2 * math.pi * k / n), 4), round(CY + r * math.sin(2 * math.pi * k / n), 4))
            for k in range(n)]


OUTLINE = ("circle", CX, CY, R_BOARD)
BOARD_THICKNESS = 1.0   # mm: keeps the LED plane low in the moon base (optics stack, FAB_NOTES)
RULES = {"clearance": 0.15, "track": 0.2, "track_min": 0.15, "via": 0.6, "drill": 0.3, "edge_clear": 1.0,
         "annular_min": 0.125, "hole_to_hole": 0.5}
NETCLASSES = [dict(name="Power", track=0.4, clearance=0.15, via=0.6, drill=0.3, nets=["VLED"])]
ROUTE_GRID = 0.05
ROUTE_OPTS = {"layer_cost": (3.0, 1.0), "via_cost_mm": 0.5}   # keep the LED face (VLED pour) intact


def _place():
    p = {}
    for ref, grp, ang in WHITE:
        a = math.radians(ang)
        # top face: KiCad y points down, so a counter-clockwise angle seen from the top is -ang in board coords
        x, y = CX + RING_R * math.cos(a), CY - RING_R * math.sin(a)
        p[ref] = (round(x, 3), round(y, 3), round(ang - 90, 2), "F")   # long axis tangential, cathode pad clockwise
    for ref, dx in RGB:
        p[ref] = (CX + dx, CY, 90, "F")
    p.update({
        "U1": (CX, CY, 90, "B"),                 # TLC59116: pin rows north/south; I2C/VCC at the north-east end
        "U2": (CX + 8.3, CY + 0.6, 90, "B"),     # LM75BDP (TSSOP-8) east, next to the I2C pins
        "R1": (CX + 5.4, CY + 4.8, 0, "B"),      # REXT next to pin 1 (south-east)
        "C1": (CX + 5.6, CY - 4.6, 0, "B"),      # VCC decoupling next to pin 28 (north-east)
        "C2": (CX - 7.6, CY + 0.0, 90, "B"),     # bulk 10 uF on VLED (west)
        "C3": (CX + 9.6, CY - 4.2, 90, "B"),     # LM75 decoupling
        "R2": (CX + 6.6, CY + 7.0, 0, "B"),      # RESET_N pull-up (LM75B OS wired-OR)
        "J1": (CX + 2.0, CY - 9.2, 180, "B"),    # cable pads, north
    })
    return p


PLACE = _place()
# GND first (it needs the channel under the TLC body to reach pins 10 and 19), then I2C, then the LED fan-in
ROUTE = [("GND", 0.3), ("SDA", 0.2), ("SCL", 0.2), ("RESET_N", 0.2), ("REXT", 0.2)] + \
        [(f"K_{w[0]}", 0.25) for w in WHITE] + [(f"K_{r[0]}_{c}", 0.2) for r in RGB for c in "RGB"] + \
        [("VLED", 0.3, {"layers": (0,)})]   # top-only tree joining every anode and the pre-stitched vias
PRE_STITCH = [("VLED", 1)]   # every bottom-side VLED pad gets a via to the top VLED pour before routing
STITCH = []                  # top face is the VLED pour: GND is routed + poured on the bottom only
STITCH_GRID = []
ZONES = [dict(net="GND", layer="B", pts=_circle(R_BOARD - 0.2), clearance=0.2, min_width=0.2),
         dict(net="VLED", layer="F", pts=_circle(R_BOARD - 0.2), clearance=0.2, min_width=0.2)]
# J1 is rotated 180: pad 1 (GND) at CX+5 ... pad 4 (SCL) at CX-1; one letter under each pad, key in the south
SILK = [dict(s=t, x=CX + 2.0 + 3.0 - 2.0 * i, y=CY - 6.9, size=0.8, thick=0.13, layer="B.SilkS")
        for i, t in enumerate("GVDC")] + \
       [dict(s="MOON LED v0.1", x=CX - 2.5, y=CY + 6.4, size=0.8, thick=0.13, layer="B.SilkS"),
        dict(s="D=SDA C=SCL", x=CX - 2.5, y=CY + 7.8, size=0.8, thick=0.13, layer="B.SilkS"),
        dict(s="2026-11", x=CX - 2.5, y=CY + 9.2, size=0.8, thick=0.13, layer="B.SilkS")] + \
       [dict(s="W" if grp == "WW" else "C",   # W = 2700 K, C = 5000 K beside each white LED (round2 R2-D10)
             x=round(CX + 10.7 * math.cos(math.radians(ang + 14)), 3),
             y=round(CY - 10.7 * math.sin(math.radians(ang + 14)), 3), size=0.8, thick=0.13, layer="F.SilkS")
        for _ref, grp, ang in WHITE]
SILK_R_MAX = 11.8            # silk stays inside the part-free radius (the r 12-13 band is clamped by the moon ring)
PAD_MAP = {}

FAB_NOTES = """# led-board v0.1 - fabrication notes (paste into the fab's order form)

- 2 layers, FR4, **1.0 mm**, 1 oz outer copper, round **26.0 mm** diameter
- Surface finish: **ENIG** (flat pads for the 2835 LEDs and TSSOP-28)
- Solder mask **WHITE** both sides (the top face is the reflector inside the moon), silkscreen black
- Min track / space 0.20 / 0.15 mm (design rule; narrowest gap on the board ~0.19 mm); vias 0.6 / 0.3 mm (drill),
  min hole 0.3 mm; no blind/buried vias
- Quantity 5. Stencils: top AND bottom (frameless, 0.12 mm; both on one foil if cheaper)
- Small round board: please leave no breakaway-tab nubs on the edge (it sits in a 26.4 mm pocket), or we sand them
- Silk: "W" = 2700 K and "C" = 5000 K next to each white LED; RGB LEDs: pad 1 ("1") = common anode, the package's
  polarity mark (pin 3, red cathode) goes on the silk chamfer
- Assembly (optional): LEDs (D1-D10) on TOP; U1 TLC59116, U2 LM75BDP, R1, R2, C1-C3 on BOTTOM. J1 = 4 solder pads for the cable
  (not a component). Two-sided assembly costs extra; or assemble the bottom only and hand-fit the ten LEDs.
"""
