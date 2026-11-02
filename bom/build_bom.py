"""Combined BOM and order lists for N complete lamps.

  python3 bom/build_bom.py [--sets 2]

Writes:
  bom/BOM.csv                 every line on both boards + off-board parts, per lamp
  bom/farnell_order.csv       Farnell UK basket (order code or MPN, quantity rounded to MOQ, with spares)
  bom/farnell_quickpaste.txt  "code, qty" lines for Farnell's Quick Paste / BOM upload
  bom/other_purchases.csv     items not sold by Farnell (battery, gooseneck, cable, nut, filament...)
  bom/ORDER.md                human summary with indicative prices
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import math
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hardware"))
sys.path.insert(0, str(ROOT / "hardware" / "tools"))
from parts import CAT  # noqa: E402

SPARES = {  # extra per order for parts that are easy to lose or damage when hand-soldering
    "R": 5, "C": 5, "LED_WW": 2, "LED_CW": 2, "LED_RGB": 1, "LED_RED_0603": 2, "LEDDRV": 1, "TEMP": 1, "MCU": 1,
    "CHG": 1, "PFET": 2, "TACT": 2, "SLIDE": 1, "USBC": 1, "JST_PH2": 1, "JST_SH4": 1, "RECT": 1, "TVS": 1,
}

# Items Farnell does not sell (or that we deliberately buy elsewhere). Prices indicative, GBP inc. VAT where retail.
OTHER = [
    dict(item="LiPo pouch 3.7 V 1200 mAh, protected, JST-PH 2.0 lead (64 x 35.5 x 5.3 mm)", qty_per_lamp=1,
         supplier="Pimoroni", code="BAT0004", url="https://shop.pimoroni.com/products/lipo-battery-pack", gbp=8.25,
         note="Alternative: The Pi Hut 105188 (62 x 35 x 5 mm). Meter polarity: + must land on J2 pin 1 (silk +)."),
    dict(item="Gooseneck 120 mm, 10 mm OD, M10x1 male ends, hollow (6.8 mm bore)", qty_per_lamp=1,
         supplier="Amazon UK (PATIKIL 4.7in M10 gooseneck)", code="search: PATIKIL gooseneck M10 120mm", url="",
         gbp=8.0, note="Backup: PATIKIL 100 mm M10/M8 (8 mm OD; bore unstated - VERIFY). Check bore >= 4.5 mm."),
    dict(item="Silicone tube 10 mm ID x 12 mm OD, 150 mm (sleeve for the gooseneck: the plastic-coated finish)",
         qty_per_lamp=1, supplier="Amazon UK / eBay (food-grade silicone tube)", code="10x12mm silicone tube 1 m",
         url="", gbp=6.0, note="Or 12 mm heat-shrink 2:1 in black/white."),
    dict(item="M10x1 brass hex nut, ~14 mm AF, 3 mm thick (moon base)", qty_per_lamp=1,
         supplier="Lamp Spares UK / any lamp-parts shop", code="M10x1 lamp nut", url="", gbp=0.5,
         note="Often supplied with the gooseneck. Measure AF/thickness (VERIFY in cad/parts/_lib/moonlib.py)."),
    dict(item="Qwiic / STEMMA QT 4-pin JST-SH cable >= 200 mm (cut one end; bare end solders to the LED board)",
         qty_per_lamp=1, supplier="RS Components", code="288-4665 (SparkFun KIT-15081 Qwiic cable kit, 50-500 mm)",
         url="https://uk.rs-online.com/web/p/cable-assemblies/2884665", gbp=11.0,
         note="Kit has several lengths: use the 200 or 500 mm one. Farnell alternative: SHR-04V-S-B housings + pre-crimped leads."),
    dict(item="M2 x 6 mm self-tapping pan-head screws (PCB to front shell)", qty_per_lamp=2, supplier="Amazon/Accu.co.uk",
         code="M2x6 self tapping pan head A2", url="", gbp=0.1, note="Accu.co.uk sells singles."),
    dict(item="M2 x 12 mm self-tapping pan-head screws (clip + back plate to front shell)", qty_per_lamp=2,
         supplier="Amazon/Accu.co.uk", code="M2x12 self tapping pan head A2", url="", gbp=0.1, note=""),
    dict(item="Filament: white PLA (moon) ~12 g, PETG (base, pack, clip, caps) ~40 g", qty_per_lamp=1,
         supplier="Bambu Lab (PLA Basic Jade White, PETG Basic)", code="", url="", gbp=1.5, note="Per lamp, filament cost."),
    dict(item="Cyanoacrylate (super glue, gel) for the gooseneck ends and the LED-pad strain relief", qty_per_lamp=0,
         supplier="any", code="", url="", gbp=3.0,
         note="Gooseneck threads only. NOT anaerobic thread-locker: it does not cure against plastic and can craze PETG (round1 m-7)."),
    dict(item="Neutral-cure silicone (or E6000): strain relief over the LED-board wire joints and the cable at J3",
         qty_per_lamp=0, supplier="any", code="", url="", gbp=5.0, note="Not acetoxy (vinegar-smell) silicone: it corrodes copper."),
    dict(item="PTFE tube 2 mm ID x 3 mm OD (or silicone sleeve), 200 mm: protects the cable inside the gooseneck",
         qty_per_lamp=1, supplier="Amazon UK / 3D-printer spares", code="PTFE tube 2x3mm", url="", gbp=0.5,
         note="Plus 6 mm heat-shrink over each cut gooseneck end (round1 M-7)."),
    dict(item="Kapton (polyimide) tape 10-20 mm: over the pouch under the PCB, and under U1/D3/Q1-Q3", qty_per_lamp=0,
         supplier="any", code="", url="", gbp=3.0, note="One roll covers many builds (round1 B-2)."),
    dict(item="USB-C charger >= 1 A at 5 V (if you don't have one)", qty_per_lamp=0, supplier="any", code="", url="",
         gbp=0.0, note="The lamp can draw ~0.5-0.6 A while charging with the light on (round1 M4)."),
]
TOOLS = [
    dict(item="UPDI programmer: Microchip MPLAB SNAP (PG164100)", supplier="Farnell", code="2915518", gbp=15.0,
         note="Or a 3.3 V USB-UART (FTDI TTL-232R-3V3, Farnell 1329311) + 470 R for SerialUPDI."),
    dict(item="Stencils (PCBWay/JLCPCB, frameless) for both boards", supplier="with the PCB order", code="", gbp=10.0, note=""),
]


def load(board):
    spec = importlib.util.spec_from_file_location(f"{board}_d", ROOT / "hardware" / board / "design.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parts()


def cat_key(part):
    for k, c in CAT.items():
        if c.mpn == part.fields.get("MPN") and c.footprint == part.footprint:
            return k
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", type=int, default=2)
    n = ap.parse_args().sets
    lines = OrderedDict()
    for board in ("main-board", "led-board"):
        for p in load(board):
            if not p.in_bom or p.dnp:
                continue
            k = cat_key(p)
            if k is None:
                raise SystemExit(f"{board} {p.ref}: no catalogue entry for MPN {p.fields.get('MPN')}")
            e = lines.setdefault(k, {"refs": [], "boards": set()})
            e["refs"].append(f"{board.split('-')[0]}:{p.ref}")
            e["boards"].add(board)
    with (ROOT / "bom" / "BOM.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Key", "Qty per lamp", "References", "Value", "Manufacturer", "MPN", "Description", "Footprint",
                    "Farnell", "Datasheet"])
        for k, e in lines.items():
            c = CAT[k]
            w.writerow([k, len(e["refs"]), " ".join(e["refs"]), c.value, c.mfr, c.mpn, c.desc, c.footprint.split(":")[-1],
                        c.farnell, c.datasheet])
        for o in OTHER:
            w.writerow(["OTHER", o["qty_per_lamp"], "", "", o["supplier"], o["code"], o["item"], "", "", o["url"]])
    total = 0.0
    rows = []
    for k, e in lines.items():
        c = CAT[k]
        need = len(e["refs"]) * n
        spare = SPARES.get(k, SPARES.get(k[0], 1))
        qty = need + spare
        moq = max(1, c.moq)
        qty = int(math.ceil(qty / moq) * moq)
        cost = qty * c.unit_gbp
        total += cost
        rows.append((c.farnell, c.mpn, c.mfr, qty, need, c.unit_gbp, cost, c.desc, k))
    with (ROOT / "bom" / "farnell_order.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Farnell Order Code", "Manufacturer Part Number", "Manufacturer", "Quantity", "Needed for builds",
                    "Indicative unit GBP (ex VAT)", "Indicative line GBP", "Description", "Line note"])
        for r in rows:
            w.writerow([r[0] or "(search MPN)", r[1], r[2], r[3], r[4], f"{r[5]:.3f}", f"{r[6]:.2f}", r[7], f"reading-light {r[8]}"])
    with (ROOT / "bom" / "farnell_quickpaste.txt").open("w") as f:
        for r in rows:
            f.write(f"{r[0] or r[1]}, {r[3]}\n")
    with (ROOT / "bom" / "other_purchases.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Item", "Qty", "Supplier", "Code / search", "URL", "Indicative GBP each", "Note"])
        for o in OTHER:
            q = o["qty_per_lamp"] * n if o["qty_per_lamp"] else 1
            w.writerow([o["item"], q, o["supplier"], o["code"], o["url"], f"{o['gbp']:.2f}", o["note"]])
        for t in TOOLS:
            w.writerow([t["item"], 1, t["supplier"], t["code"], "", f"{t['gbp']:.2f}", t["note"]])
    other = sum((o["qty_per_lamp"] * n if o["qty_per_lamp"] else 1) * o["gbp"] for o in OTHER)
    tools = sum(t["gbp"] for t in TOOLS if t["supplier"] != "with the PCB order")   # stencils are in the PCB line
    md = [f"# Order summary: {n} lamps (generated by `python3 bom/build_bom.py --sets {n}`; do not edit by hand)", "",
          "Indicative prices from Farnell UK listings and seller pages, 2026-11. **Matt places every order.** After ordering,",
          "record the actual codes and prices in `bom/ORDER_ACTUALS.md` (handoff 02).", "",
          "## 1. Farnell UK basket",
          f"Upload `bom/farnell_quickpaste.txt` (Quick Paste / BOM upload). {len(rows)} lines, quantities include spares and",
          "MOQ rounding. Lines without an order code are listed by MPN: pick that exact MPN on the site (substitution rules",
          "in handoff 02).", "",
          "| Farnell code | MPN | Manufacturer | Qty | Needed | Line GBP ex VAT | What |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r[0] or '(search MPN)'} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[6]:.2f} | {r[7].split(',')[0]} |")
    md += ["", f"**Farnell subtotal ≈ £{total:.2f} ex VAT (≈ £{total * 1.2:.2f} inc VAT).**", "",
           "## 2. Other purchases (not Farnell)", "",
           "| Item | Qty | Supplier | Code / search | GBP each | Note |", "|---|---|---|---|---|---|"]
    for o in OTHER:
        q = o["qty_per_lamp"] * n if o["qty_per_lamp"] else 1
        md.append(f"| {o['item']} | {q} | {o['supplier']} | {o['code']} | {o['gbp']:.2f} | {o['note']} |")
    md += ["", f"**Other subtotal ≈ £{other:.2f}.**", "", "## 3. Tools (once)", "",
           "| Item | Supplier | Code | GBP | Note |", "|---|---|---|---|---|"]
    for t in TOOLS:
        md.append(f"| {t['item']} | {t['supplier']} | {t['code']} | {t['gbp']:.2f} | {t['note']} |")
    md += ["", "## 4. PCBs (handoff 01; route comparison in `bom/assembly_routes.md`)", "",
           "Recommended route 1: 5 main + 5 LED bare boards with stencils from PCBWay (≈ £40–60 incl. shipping), or",
           "JLCPCB (≈ £15–35). Upload `fab/<board>/v0.1/<board>-v0.1-gerbers.zip` and copy the specs from each",
           "`FAB_NOTES.md`.", "",
           "## 5. Total for this build (route 1)", "",
           f"Farnell ≈ £{total * 1.2:.0f} + other ≈ £{other:.0f} + programmer ≈ £{tools:.0f} (if needed) + PCBs ≈ £15–60 "
           f"→ **≈ £{total * 1.2 + other + 15:.0f}–{total * 1.2 + other + tools + 60:.0f} for {n} lamps.**", ""]
    (ROOT / "bom" / "ORDER.md").write_text("\n".join(md))
    print(f"{len(rows)} Farnell lines, indicative GBP {total:.2f} ex VAT for {n} lamps (+ spares); other purchases ~GBP {other:.2f}")
    return rows, total, other


if __name__ == "__main__":
    main()
