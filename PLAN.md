# PLAN — Moon reading light

Status: **v0.1 design complete, nothing ordered** (2026-11-02). Next: Matt orders boards + parts, prints, builds
(docs/handoffs/). Single source of truth for requirements and decisions; reasoning is kept so later revisions don't
re-derive it.

---

## 1. Requirements

Statuses follow the 3dprint convention: **GIVEN** (Matt said it), **ASSUMED** (Claude's reading; confirm), **RULE**
(engineering rule this design adopts).

| # | Status | Requirement |
|---|---|---|
| R1 | GIVEN | Clip-on reading light: a pack clips onto the back of a book with a slip-on clip |
| R2 | GIVEN | Pack holds the battery and electronics; enclosed mini LiPo, USB-C charging |
| R3 | GIVEN | From the top of the pack a flexible, adjustable neck ~10 cm long |
| R4 | GIVEN | At the end of the neck a hollow model of the moon, ~5 cm diameter, lit fully from inside by LEDs |
| R5 | GIVEN | One main button: press turns the light on/cycles colours (answer 3: the button never turns it off) |
| R6 | GIVEN | Hold the main button > 2 s: sets the current colour as the power-on default |
| R7 | GIVEN | Slide on/off switch on the side is the only on/off (answer 3) |
| R8 | GIVEN | Up and down brightness buttons above and below the main button |
| R9 | GIVEN | Colours: soft white, blue-white, yellow/orange/natural white, soft orange night light, red, green, blue; research and add other night-light whites |
| R10 | GIVEN | Moon model generated from NASA data (answer 5), Thingiverse surveyed |
| R11 | GIVEN | LED design: CRI-90+ tunable white + RGB with a constant-current driver (answer 1); LEDs in the base of the moon at the top of the neck |
| R12 | GIVEN | Neck: pre-made metal, plastic-coated bendable arm |
| R13 | GIVEN | Battery ~1200 mAh (answer 4) |
| R14 | GIVEN | PCB files ready for PCBWay (or another fab); print files ready for the printer (Bambu X2D); BOM + order list for Farnell or RS |
| R15 | GIVEN | Use the 14MM47/pcb and 14MM47/3dprint processes; product files live in this repo (answer 6) |
| R16 | GIVEN | Multiple verification runs against datasheets, with adversarial/specialist reviewers |
| R17 | RULE | Slide switch off = battery isolated from everything except the charger: standby drain < 10 µA |
| R18 | RULE | LiPo charged CC/CV 4.20 V at ≤ 0.5 C; reverse-battery protected; load sharing so charging terminates with the light on |
| R19 | RULE | Flicker-free (PWM ≥ 20 kHz) and no PLA moon softening: LED-board temperature limited in firmware with a sensor |
| R20 | RULE | Night modes contain no green or blue light (melanopic research); whites on the Planckian locus |
| R21 | ASSUMED | Hand-assembly friendly parts (0603+, SOIC/TSSOP, no QFN/BGA) so all three assembly routes work |
| R22 | ASSUMED | Pack ≤ ~45 × 80 × 20 mm, total mass ≤ ~100 g |

## 2. Architecture

```
 USB-C (power only, 5.1k CC) ─TVS─┬─> MCP73831 charger 417 mA ─> BAT ─[Q3 rev-batt P-FET]─ LiPo 1200 mAh (own PCM)
                                  └─> D3 S1J rectifier ─┐
 BAT ─[Q1 load-share P-FET, gate = VBUS]────────────────┴─> VSYS_RAW ─[Q2 P-FET, slide switch]─> VSYS 3.3–4.2 V (4.15 on USB)
 VSYS ─> ATtiny3216 (buttons, I2C master, VDD measurement) ─ JST-SH 4-wire cable up the gooseneck ─┐
                                                                                                    v
   LED board in the moon base (26 mm): TLC59116 16-ch constant-current sink, 25 mA/channel, 97 kHz PWM
   ├─ 4 × 2700 K + 4 × 5000 K Bridgelux Thrive 2835 (CRI 97)      ├─ 2 × Würth RGB (common anode)
   └─ LM75B temperature sensor (firmware derating)                  all anodes on VLED = VSYS
```

* **Main board** (pack, 35 × 62 mm, 2-layer 1.6 mm, all parts top): see `hardware/main-board/design.py` docstring.
* **LED board** (moon base, Ø26 mm, 2-layer 1.0 mm, white mask; LEDs top, driver/sensor bottom): `hardware/led-board/design.py`.
* **Optics**: a Lambertian source on the wall of a sphere lights its inside uniformly (integrating-sphere geometry).
  Model `docs/design/optics/sphere_illum.py`: with the LED plane 1–2 mm below a 30–36° opening, wall illuminance
  max/min ≈ 1.00–1.05 and ~97 % of the LED flux reaches the wall. Raising the board above the opening gives ≥ 2:1.
* **Firmware**: `firmware/` — portable core (`lib/core`) + hardware glue (`src/main.cpp`); modes from
  `tools/gen_modes.py` (CIE 1931 mixing to the Planckian locus).
* **Mechanics**: lithophane moon (PLA, NASA LROC albedo + LOLA relief → 0.9–2.6 mm wall, relief inside),
  bayonet-locked to a PETG base cup that clamps the LED board and screws onto the gooseneck's M10×1 end;
  pack = front shell + back plate + slip-on cantilever clip (PETG).

## 3. Light modes (R9, R20)

Ten modes in button order (`firmware/include/modes_table.h`, generated): Warm 2700 K · Soft white 3000 K ·
Neutral reading 4000 K · Daylight 5000 K · Blue-white 6500 K · Candle 1900 K · Soft orange night · Red night ·
Green · Blue. Evidence and targets: `docs/research/light-modes.md` (melanopic EDI limits from Brown et al. 2022,
red for dark adaptation, Planckian chromaticities). 16 brightness steps, geometric 0.4 %–100 %. Power-on default:
Soft white 3000 K at level 10 until the user saves another.

## 4. Decision log

- 2026-11-02 — Product files in `reading_light`; process conventions from `14MM47/pcb` and `14MM47/3dprint` (Matt, answer 6).
- 2026-11-02 — LEDs in the moon base facing up (Matt's suggestion); confirmed by the optics model (uniform within ~1 %).
- 2026-11-02 — Slide switch is the only on/off; main button never turns off (Matt, answer 3).
- 2026-11-02 — Farnell UK chosen over RS (wider semiconductor range, Adafruit/TI/Microchip stock); RS only as fallback.
- 2026-11-02 — LED driver TLC59116 (Farnell 3119169) instead of TI LP5012 (not stocked by Farnell/RS). Cost: 25–37 mA
  driver supply current while on; 8-bit PWM (+ IREF gain for low-end resolution).
- 2026-11-02 — Cool white is 5000 K (only CRI-90+ cool 2835 at Farnell); 6500 K is mixed with blue + a little green.
- 2026-11-02 — RGB LED Würth 150141M173100 (datasheet + exact KiCad footprint) instead of Kingbright KAAF-5050
  (datasheet unobtainable → pinout unverifiable). Würth abs max 30 mA → TLC59116 REXT 750 Ω = 25.0 mA/channel.
- 2026-11-02 — Two RGB LEDs (14 of 16 driver channels) to double red for candle/night modes.
- 2026-11-02 — USB→system OR-ing uses an S1J silicon rectifier, not a Schottky: MBR120VLSF reverse leakage (0.6 mA max
  @25 °C) would drain the cell through the load-share FET while switched off. Cost: VSYS ≈ 4.15 V on USB.
- 2026-11-02 — 10 µF capacitors are 0805 16 V (0603 10 V keeps only ~2.9 µF at 5 V per Samsung's DC-bias data).
- 2026-11-02 — LED board Ø26 mm (moon opening 33° instead of 30°): the 24 mm board could not be routed; optics model
  shows no uniformity change (max/min 1.001 at the chosen depth).
- 2026-11-02 — LM75BDP (TSSOP-8) instead of LM75BD (SOIC-8) to fit the LED board.
- 2026-11-02 — Moon relief on the inside, smooth 50.0 mm outside (crisp silhouette; outer overhangs ≤ 45° by claim).
- 2026-11-02 — Gooseneck: 120 mm, 10 mm OD, M10×1 ends, 6.8 mm bore (no coated gooseneck of this length is sold in
  the UK); sleeve it in silicone/heat-shrink for the plastic-coated look and feel (R12).

## 5. Open questions / VERIFY

See `docs/verification/VERIFY.md` (measurements that only the prototype can settle).

## 6. Status

| Phase | Deliverable | Status |
|---|---|---|
| Requirements & research | this file, docs/research | done |
| Electronics | hardware/*, ERC/DRC clean | done (v0.1) |
| Firmware | firmware/, host tests + AVR build | done (v0.1), untested on hardware |
| Mechanics | cad/parts, print/ | in progress |
| Verification rounds | docs/verification | round 1 running |
| BOM/order, handoffs | bom/, docs/handoffs | pending |
