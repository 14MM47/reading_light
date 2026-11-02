"""Main board (in the clip-on pack): USB-C charging, battery protection/load sharing, slide power switch,
ATtiny3216, three buttons, I2C to the LED board in the moon.

Single source of truth for the schematic (kigen.schematic) and the board (kigen.board). Net names follow
the pcb repo conventions (upper-case, + for positive rails avoided because KiCad labels treat it literally).

Power tree (see docs/design/electronics.md):
  USB-C VBUS --TVS--+--> MCP73831 VDD --(CC/CV 4.20 V, ~417 mA)--> BAT --Q3 (reverse-battery P-FET)--> BAT_RAW = cell
                    +--> D3 silicon rectifier (low leakage) -----+
                                                                 +--> VSYS_RAW --Q2 (slide-switch load switch)--> VSYS
  BAT --Q1 (load-share P-FET, off while VBUS present)-----------+
  VSYS feeds the MCU and, through the JST-SH cable, the LED board (VLED).
"""
from __future__ import annotations

import sys
from pathlib import Path

HW = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HW / "tools"))
sys.path.insert(0, str(HW))
from kigen.schematic import Part  # noqa: E402
from parts import CAT  # noqa: E402

PROJECT = "main-board"
TITLE = "Moon reading light - main board (pack)"
REV = "0.1"


def P(ref, cat, pins, sch, lib_id=None, value=None, footprint=None, **kw):
    c = CAT[cat]
    fields = {"MPN": c.mpn, "Manufacturer": c.mfr, "Farnell": c.farnell, "Datasheet": c.datasheet,
              "Description": c.desc}
    return Part(ref, lib_id or LIB[cat], value or c.value, footprint or c.footprint, pins, sch=sch, fields=fields, **kw)


LIB = {
    "MCU": "MCU_Microchip_ATtiny:ATtiny3216-S", "CHG": "Battery_Management:MCP73831-2-OT",
    "PFET": "Transistor_FET:Q_PMOS_GSD", "SCHOTTKY": "Device:D_Schottky", "RECT": "Device:D", "TVS": "Device:D_Zener",
    "LED_RED_0603": "Device:LED", "USBC": "Connector:USB_C_Receptacle_PowerOnly_6P", "TACT": "Switch:SW_Push",
    "SLIDE": "Switch:SW_SPDT", "JST_PH2": "Connector_Generic:Conn_01x02", "JST_SH4": "Connector_Generic:Conn_01x04",
    "R_5K1": "Device:R", "R_2K4": "Device:R", "R_1K": "Device:R", "R_10K": "Device:R", "R_100K": "Device:R",
    "R_1M": "Device:R", "R_3K3": "Device:R", "C_100N": "Device:C", "C_1U": "Device:C", "C_4U7": "Device:C",
    "C_10U": "Device:C",
}


def parts():
    v = []
    # ---- A: USB-C input, ESD, charger (sheet top-left)
    v += [
        P("J1", "USBC", {"A5": "CC1", "B5": "CC2", "A9": "VBUS", "B9": "VBUS", "A12": "GND", "B12": "GND", "S1": "GND"},
          (40, 70, 0)),
        P("R1", "R_5K1", {"1": "CC1", "2": "GND"}, (75, 90, 0)),
        P("R2", "R_5K1", {"1": "CC2", "2": "GND"}, (85, 90, 0)),
        P("D1", "TVS", {"1": "VBUS", "2": "GND"}, (100, 85, 270), value="SMF5.0A"),
        P("C1", "C_10U", {"1": "VBUS", "2": "GND"}, (112, 85, 0)),
        P("U1", "CHG", {"1": "CHG_STAT", "2": "GND", "3": "BAT", "4": "VBUS", "5": "PROG"}, (150, 80, 0)),
        P("R3", "R_2K4", {"1": "PROG", "2": "GND"}, (128, 100, 0)),
        P("R4", "R_1K", {"1": "VBUS", "2": "CHG_LED"}, (178, 55, 90)),
        P("D2", "LED_RED_0603", {"1": "CHG_STAT", "2": "CHG_LED"}, (178, 72, 90), value="red"),
        P("C2", "C_10U", {"1": "BAT", "2": "GND"}, (190, 95, 0)),
    ]
    # ---- B: battery, reverse protection, load share, power switch (sheet top-right)
    v += [
        P("J2", "JST_PH2", {"1": "BAT_RAW", "2": "GND"}, (225, 70, 0),
          value="BATTERY (+ = pin 1)"),
        P("Q3", "PFET", {"1": "Q3_G", "2": "BAT", "3": "BAT_RAW"}, (255, 60, 0), value="DMG2305UX"),
        P("R10", "R_10K", {"1": "Q3_G", "2": "GND"}, (247, 82, 0)),
        P("Q1", "PFET", {"1": "VBUS", "2": "VSYS_RAW", "3": "BAT"}, (295, 60, 0), value="DMG2305UX"),
        P("R5", "R_100K", {"1": "VBUS", "2": "GND"}, (282, 85, 0)),
        P("D3", "RECT", {"1": "VSYS_RAW", "2": "VBUS"}, (300, 100, 0), value="S1J"),
        P("C3", "C_10U", {"1": "VSYS_RAW", "2": "GND"}, (322, 90, 0)),
        P("Q2", "PFET", {"1": "SW_GATE", "2": "VSYS_RAW", "3": "VSYS"}, (360, 60, 0), value="DMG2305UX"),
        P("R6", "R_1M", {"1": "VSYS_RAW", "2": "SW_GATE"}, (340, 85, 0)),
        P("C5", "C_100N", {"1": "VSYS_RAW", "2": "SW_GATE"}, (350, 85, 0)),
        P("R7", "R_10K", {"1": "SW_GATE", "2": "SW_COM"}, (365, 100, 90)),
        P("SW1", "SLIDE", {"1": "GND", "2": "SW_COM", "3": "VSYS_RAW"}, (390, 110, 0), value="PCM12 ON/OFF"),
        P("C4", "C_10U", {"1": "VSYS", "2": "GND"}, (395, 70, 0)),
    ]
    # ---- C: MCU, programming header, test points (sheet bottom-left)
    # pins chosen for the layout: PA6/PA5/PA4 run top-to-bottom beside the UP/MAIN/DOWN buttons;
    # debug TX uses USART0's alternate pin PA1 (PORTMUX), next to UPDI and the header
    mcu = {"1": "VSYS", "20": "GND", "16": "UPDI", "17": "TX", "18": None, "19": None,
           "2": "BTN_DN", "3": "BTN_MAIN", "4": "BTN_UP", "5": None,
           "11": "SCL", "10": "SDA", "9": None, "8": None, "7": None, "6": None,
           "12": None, "13": None, "14": None, "15": None}
    v += [
        P("U2", "MCU", mcu, (90, 215, 0), value="ATtiny3216-SN"),
        P("C6", "C_100N", {"1": "VSYS", "2": "GND"}, (45, 200, 0)),
        P("C7", "C_1U", {"1": "VSYS", "2": "GND"}, (55, 200, 0)),
        Part("J4", "Connector_Generic:Conn_01x04", "UPDI/TX", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
             {"1": "VSYS", "2": "UPDI", "3": "TX", "4": "GND"}, sch=(150, 200, 0),
             fields={"Description": "Programming header (SerialUPDI / MPLAB Snap) + debug TX; pins fitted only for programming",
                     "MPN": "DNP", "Farnell": ""}, in_bom=False, dnp=True),
    ]
    for i, (net, x) in enumerate([("VBUS", 130), ("BAT_RAW", 142), ("VSYS", 154), ("GND", 166), ("SDA", 178),
                                  ("SCL", 190)], 1):
        v.append(Part(f"TP{i}", "Connector:TestPoint", net, "TestPoint:TestPoint_Pad_D1.5mm", {"1": net},
                      sch=(x, 250, 0), fields={"Description": "Test pad", "MPN": "-", "Farnell": ""}, in_bom=False))
    # ---- D: buttons, I2C pull-ups, moon connector (sheet bottom-right)
    v += [
        P("SW2", "TACT", {"1": "BTN_UP", "2": "GND"}, (240, 180, 0), value="UP"),
        P("SW3", "TACT", {"1": "BTN_MAIN", "2": "GND"}, (240, 200, 0), value="MAIN"),
        P("SW4", "TACT", {"1": "BTN_DN", "2": "GND"}, (240, 220, 0), value="DOWN"),
        P("R8", "R_3K3", {"1": "VSYS", "2": "SDA"}, (300, 200, 0)),
        P("R9", "R_3K3", {"1": "VSYS", "2": "SCL"}, (310, 200, 0)),
        P("J3", "JST_SH4", {"1": "GND", "2": "VSYS", "3": "SDA", "4": "SCL"}, (360, 205, 0),
          value="MOON (Qwiic pinout, VCC=VSYS)"),
    ]
    return v


# footprint pad -> symbol pin, where they differ
PAD_MAP = {
    "J2": {"MP": None},   # mechanical pads: no net
    "J3": {"MP": None},
}

PWR_FLAGS = [("VBUS", (60, 40)), ("GND", (70, 40)), ("BAT_RAW", (215, 40)), ("VSYS_RAW", (330, 40)),
             ("VSYS", (400, 40))]

NOTES = [
    ("A  USB-C input, ESD and charger", (12, 25)),
    ("B  Battery, reverse-battery FET, load sharing, slide power switch", (212, 25)),
    ("C  MCU, programming header, test pads", (12, 160)),
    ("D  Buttons, I2C pull-ups, moon cable", (212, 160)),
]
BOXES = [(10, 20, 205, 150), (210, 20, 410, 150), (10, 155, 205, 285), (210, 155, 410, 285)]
COMMENTS = [
    "Charge 417 mA (R3 2.4k). Slide switch is the only on/off (Matt). VSYS 3.3-4.2 V on battery, ~4.15 V on USB.",
    "J3 carries VSYS (not 3.3 V) on the Qwiic pinout: never plug a 3.3 V-only Qwiic device into it.",
    "J2 polarity: + on pin 1 (silk). Q3 blocks a reversed battery; meter every pack before plugging in.",
]


# ============================================================================ PCB
# Board 35 x 62 mm, 1.6 mm FR4, 2 layers, all parts on top (single-sided assembly).
# Origin top-left, y down. Top edge = neck end of the pack; USB-C on the bottom edge; slide switch on the right edge.
W, H, RC = 35.0, 62.0, 2.0


def _rounded_rect(w, h, r, n=6):
    import math
    pts = []
    for cx, cy, a0 in ((w - r, r, -90), (w - r, h - r, 0), (r, h - r, 90), (r, r, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((round(cx + r * math.cos(a), 4), round(cy + r * math.sin(a), 4)))
    return pts


OUTLINE = ("poly", _rounded_rect(W, H, RC))
RULES = {"clearance": 0.2, "track": 0.25, "track_min": 0.2, "via": 0.6, "drill": 0.3, "edge_clear": 0.3,
         "annular_min": 0.15, "hole_to_hole": 0.5}
POWER_NETS = ["VBUS", "BAT", "BAT_RAW", "VSYS_RAW", "VSYS"]
NETCLASSES = [dict(name="Power", track=0.5, clearance=0.2, nets=POWER_NETS)]

PLACE = {
    # ref: (x, y, rot, side)
    "J3": (17.5, 3.6, 180, "F"),            # JST-SH to the moon, opening faces the top edge
    "R9": (12.5, 4.5, 90, "F"), "R8": (14.2, 8.6, 0, "F"),   # SCL / SDA pull-ups on the MCU side of J3
    "TP6": (8.5, 4.0, 0, "F"), "TP5": (9.0, 8.5, 0, "F"),
    "TP4": (3.5, 12.0, 0, "F"),
    "Q2": (29.5, 11.0, 0, "F"), "C4": (25.5, 11.0, 90, "F"), "TP3": (32.5, 6.0, 0, "F"),
    "R6": (30.5, 15.5, 0, "F"), "C5": (30.5, 17.5, 0, "F"), "R7": (27.0, 20.5, 90, "F"),
    "SW2": (17.5, 17.0, 0, "F"), "SW3": (17.5, 28.0, 0, "F"), "SW4": (17.5, 39.0, 0, "F"),
    "SW1": (32.85, 28.0, 90, "F"),          # slide switch, knob out of the right edge
    "U2": (6.0, 26.0, 180, "F"),            # pin 1 bottom-right: PA4-6 (buttons) face the buttons, PB0/1 (I2C) at the top
    "C6": (8.0, 34.6, 0, "F"), "C7": (4.0, 34.6, 0, "F"),
    "J4": (3.0, 38.6, 0, "F"),
    "Q3": (28.5, 33.5, 90, "F"), "R10": (25.0, 33.5, 90, "F"),
    "Q1": (28.5, 38.5, 0, "F"), "C3": (32.8, 38.5, 90, "F"),
    "R5": (24.0, 41.5, 90, "F"), "D3": (29.0, 43.8, 0, "F"),
    "TP1": (32.5, 47.0, 0, "F"), "TP2": (9.0, 47.0, 0, "F"),
    "U1": (29.0, 51.0, 90, "F"), "R3": (32.8, 51.0, 90, "F"), "C2": (25.0, 51.0, 90, "F"),
    "C1": (21.5, 50.5, 0, "F"), "D1": (14.0, 50.5, 0, "F"),
    "R1": (11.0, 56.0, 90, "F"), "R2": (24.0, 56.5, 90, "F"),
    "J1": (17.5, 58.6, 0, "F"),
    "D2": (27.5, 59.2, 0, "F"), "R4": (31.0, 59.2, 0, "F"),
    "J2": (4.9, 54.5, 270, "F"),            # battery connector, opening faces the left edge
}

ROUTE = [
    # (net, width) in order; GND is poured on both layers and stitched
    ("VBUS", 0.5), ("BAT", 0.5), ("BAT_RAW", 0.5), ("VSYS_RAW", 0.5), ("VSYS", 0.5),
    ("SCL", 0.25), ("SDA", 0.25),
    ("CC1", 0.25), ("CC2", 0.25), ("PROG", 0.25), ("CHG_STAT", 0.25), ("CHG_LED", 0.25),
    ("Q3_G", 0.25), ("SW_GATE", 0.25), ("SW_COM", 0.25),
    ("BTN_UP", 0.25), ("BTN_MAIN", 0.25), ("BTN_DN", 0.25),
    ("UPDI", 0.25), ("TX", 0.25),
]
STITCH = [("GND", 0)]
STITCH_GRID = [("GND", 3.0)]
_board_poly = _rounded_rect(W, H, RC)
ZONES = [dict(net="GND", layer="B", pts=_board_poly, clearance=0.25),
         dict(net="GND", layer="F", pts=_board_poly, clearance=0.3, priority=0)]
SILK = [
    dict(s="MOON LIGHT main v0.1 2026-11", x=17.5, y=31.0, size=0.8, thick=0.12, layer="B.SilkS"),
    dict(s="+", x=1.2, y=52.5, size=1.0, thick=0.15),
    dict(s="UPDI: 1=VSYS 2=UPDI 3=TX 4=GND", x=17.5, y=33.5, size=0.8, thick=0.13, layer="B.SilkS"),
]

# M2 mounting holes (PCB hangs from two bosses on the inside of the pack's front face; keep Ø5.5 clear on top)
MOUNT_HOLES = [(21.5, 10.0), (17.5, 46.5)]
