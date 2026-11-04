# LED board v0.2 and the slim moon head (2026-11-03)

Matt's brief, in order: make the cap that joins the moon to the gooseneck smaller so it takes less of the moon;
keep the driver on the LED board (not the pack); find a smaller driver; fewer LEDs on a smaller ring if the light
stays even. Decision: **TI LP5012 on an 18 mm board, routed, with the head redesigned around it** ("go with LP5012,
route the Ø18 board and fold in the full redesign").

Source of truth: `hardware/led-board/design.py` (board), `cad/parts/_lib/moonlib.py` and the head parts (mechanics),
`firmware/` (driver layer). This note keeps the reasoning.

## 1. What changed

| | v0.1 | v0.2 |
|---|---|---|
| LED board | Ø26 mm, TLC59116 (TSSOP-28) + LM75BDP (TSSOP-8), 0603 | **Ø18 mm**, LP5012 (WQFN-20, 3 × 3 mm) + MCP9800A0 (SOT-23-5), 0402 |
| LEDs | 4 + 4 white 2835 on a ring, 2 Würth RGB | 4 + 4 white 2835 radial on a ring of **radius 5.8 mm**, **1** Würth RGB at the centre |
| Driver channels | 14 of 16 used, 25 mA, 97 kHz 8-bit | 11 of 12 used, 25 mA, 29 kHz 12-bit (9 + 3 dither) |
| Driver supply current while lit | up to 29 mA | 4–6 mA (datasheet §7.5; §8.4 says 10 mA typ; ≤ 10 µA in power-save) |
| Hardware thermostat | LM75B OS → TLC RESET | MCP9800 ALERT → LP5012 EN (60/52 °C) |
| Board rules | 0.2 / 0.2 mm | **0.15 / 0.15 mm**, ENIG, 0.10 mm bottom stencil |
| Cap below the moon | PETG cup Ø38.7 mm, wider than the moon's Ø33.3 cut | moon's own skirt **Ø25.3 mm**; the PETG cup (Ø20.8, lugs Ø22.4) sits inside it |
| Moon surface given up to the base | ~13 % of the sphere (cut at 41.9° from the bottom pole; the cup's silhouette hid ~18 %) | **~7 %** (skirt at 30.4°) |
| Opening / LED depth | r 12.3 (33°), LEDs 2.9 mm below | r 9.0 (23.7°), LEDs 1.2 mm below |
| Wall uniformity, corrected model (§5) | 1.068 one white, 1.063 all whites, 1.054 RGB | **1.028, 1.021, 1.037** |
| Moon lock | anticlockwise twist; cup held by one nut | **clockwise** twist (jar lid; tightens the thread); cup jammed between two nuts; the ring is a designed spring |

The main board is unchanged (v0.1). The firmware changed for the new driver and sensor; the I²C bus, the four-wire
cable and its pinout are the same.

## 2. Driver: TI LP5012

Why it, against the others looked at (docs/research/sourcing-farnell-rs.md): 12 channels in 3 × 3 mm, runs from
2.7 V (the TLC59116 and PCA9955B need 3.0 V), 4–6 mA supply current instead of up to ~29 mA (with v0.1's 750 Ω REXT), one resistor sets the
current, and its EN pin gives the thermostat a hard shutdown. Against it: WQFN-20 at 0.4 mm pitch with an exposed pad
(no iron soldering, R21 revised), and neither Farnell nor RS stocks it, so it comes from DigiKey UK
(`bom/digikey_order.csv`).

Facts used (datasheet SLVSEH2B, extract in docs/datasheets/KEYSPECS.md):
- I_OUT = 105 × 0.7 V / R_IREF; R1 = **2.94 kΩ → 25.0 mA** (Würth RGB abs max 30 mA). Max_Current_Option stays 0.
- ADDR1 = ADDR0 = GND → **0x14**. DEVICE_CONFIG1 = 0x1C (log scale off, power save on, auto-increment on, PWM
  dithering on). Chip_EN in DEVICE_CONFIG0 must be set after every power-up or EN release; the firmware reads it back
  every second and re-inits on 0.
- Duty = OUTx_COLOR × LEDx_BRIGHTNESS (linear). Each LEDx_BRIGHTNESS covers three adjacent outputs, and here every
  bank mixes groups, so the firmware writes one brightness to all four banks and the per-group ratio in the colours
  (`lp_brightness()` / `lp_colour()` in `lib/core`, with hysteresis and write ordering, host-tested).
- Headroom V_SAT 0.25 V typ / 0.35 V max (specified at 20 mA; likely ~0.3–0.45 V at 25 mA). Whites and red are
  regulated over the whole battery range; a typical green or blue die (V_F ~3.3 V) drops out of regulation below
  about 3.7 V of battery, and a maximum-V_F die (~3.7 V at 25 mA) needs ~4.05–4.15 V, so it is never fully regulated
  (round3 R3-E3; §7).
- VCAP 1 µF (C4) for the internal LDO, VCC 1 µF (C1), 10 µF bulk (C2) on VLED. C4 and R1 sit within 5 mm of U1, but
  their ground returns to U1's exposed pad run ~22–26 mm round the I²C bundle (round3 R3-E2): TI asks for them
  "as close as possible". The DC error is ~0.2 %; VERIFY E18 scopes VCAP, and the next revision should add EP vias
  and a short GND jumper. IREF is fixed copper from the pad centres (R3-E1).
- The datasheet's OUTx_COLOR tables say FFh = 0 %, against its bank tables, reset defaults and power-save text; the
  design takes FFh = 100 %, and the init zeroes every output in standby before enabling the chip, so it is safe
  either way. VERIFY E8 checks the polarity.

## 3. Temperature sensor: MCP9800A0

The LM75BDP (TSSOP-8, 3 × 4.9 mm with leads) did not fit the bottom face. The TMP1075 (WSON-8, 2 × 2 mm) fits but
its pins run SDA, SCL, ALERT in ascending order: placed on the same face as the LP5012, whose SDA/SCL/EN run the
other way, the three lines must cross, and there is no room for a via pair. The MCP9800A0 (SOT-23-5) has pin 5 SDA,
4 SCL, 3 ALERT, so the bundle arrives in order, and SCL passes under its body to the cable pad. It is LM75 register
compatible (temperature, CONFIG, THYST, TSET at 0x48), stocked at Farnell (1439485), ±1 °C max from −10 to 85 °C,
200 µA typical. A 12-bit conversion takes up to 600 ms, so the firmware trusts the first reading after 700 ms.

Configuration written at every init: CONFIG 0x68 (12-bit, fault queue 2, comparator mode, ALERT active low), TSET
60 °C, THYST 52 °C. Its power-on defaults (80/75 °C) are a looser backstop until then. ALERT is open drain; the EN
pull-up R2 (2.4 kΩ, round2 R2-E5) had no room on the bottom face, so it is an 0402 on the **top** face in the outer gap
between D1 and D2 (one more part to hand-fit on top).

## 4. Layout

- **LED ring.** 2835s point radially with the cathode pad inward at r 5.8 mm; their bodies reach r 7.68 (pad corners
  r 7.88), inside the r 7.8 body limit set by the clamp band (r 8–9 mm carries no copper: the PETG ring and the cup's ledge clamp it). With
  KiCad's standard 2835 courtyard, eight of them overlapped on a ring this small, so the project footprint
  `LED_PLCC_2835_Dense` keeps KiCad's land pattern with an IPC level-C (0.1 mm) courtyard. WW and CW alternate at
  22.5° + 45°·k; the RGB sits at the centre, inside the ring of cathode pads.
- **Cathodes and fan-in.** Every cathode drops through a via (r 3.25 on the LED's centreline, the two north LEDs on
  the ring bisectors at r 3.6 to open a gap) onto the bottom face, where the LP5012 sits at the centre. The outputs are
  assigned in planar clockwise order (`assign_outputs()`), so the fan-in has no crossings; it is fixed copper in
  `design.py` (`fanin_tracks()`, checked by `_check_fanin()`), because the greedy router took the wrong side of the
  vias every time. `board_map.h` is generated from that assignment as before.
- **Control side.** The LP5012's VCC/SDA/SCL/EN/IREF pins face north into the wide gap; the I²C/EN bundle to the
  cable pads and the MCP9800 is pre-routed (`bundle_tracks()`). The router does IREF, VCAP, GND and VLED only, with a
  GND pour on the bottom and a VLED pour on the top.
- **Rules.** The WQFN's middle pins cannot escape at 0.2 mm, so the board uses 0.15 / 0.15 mm (below the pcb repo's
  0.2 mm working minimum, still inside both fabs' standard rules of 0.1–0.127 mm), and the router's grid is aligned
  to the driver's centre so its pads sit on cell centres.
- **Cable pads** J1: 2 × 2 pads 1.2 mm on a 1.9 mm pitch on the bottom, silk G V D C (GND, VLED, SDA, SCL; the same
  four wires as v0.1).
- **kigen changes** (all inert for the main board, which still routes clean): router grid alignment
  (`ROUTE_ALIGN`), `stitch_pads(skip_connected=...)`, optional nets that a pour may finish (`ROUTE` option
  `optional`), `board_map.h` carries `N_OUT`.

Result: ERC 0, DRC 0 violations, 0 unconnected, 0 parity. Fab files in `fab/led-board/v0.2/`
(`fab/led-board/v0.1/` was removed: never ordered).

## 5. Optics, and a correction

The opening in the moon's bottom is the aperture. An earlier sweep in this session modelled a 30° flared bore and
reported 1.01 max/min at 2.9 mm depth, but its ray test let light pass a flare that was **wider than the opening at the
cut plane**, which is to say through the PLA wall. With the opening as the aperture (`docs/design/optics/head_v02.py`,
output `head_v02.txt`), the depth of the LEDs below the opening is what matters: deeper LEDs shade the low wall.

| Head | LED depth below opening | max/min, one white | all whites | RGB |
|---|---|---|---|---|
| v0.2 as built, opening r 9.0 | 1.0 mm | 1.029 | 1.021 | 1.044 |
| **v0.2 as built, opening r 9.0** | **1.2 mm** | **1.028** | **1.021** | **1.037** |
| v0.2 as built, opening r 9.0 | 2.0 mm | 1.077 | 1.075 | 1.018 |
| v0.2, opening r 8.3 (board − 0.7) | 2.9 mm | 1.209 | 1.180 | 1.002 |
| v0.1, opening r 12.3, 2 RGB | 2.9 mm | 1.068 | 1.063 | 1.054 |

Round 3 (R3-O1/O2) added the RGB package at the centre as an occluder for the white LEDs' low rays (it stands 1.2 mm
above their emitters) and the slant of the wall in the 40–50° band to the area element (checked against flux
conservation: 1.000 for a centre source, 0.983 vs an analytic 0.9825 for an LED under the aperture). That moved the
whites from 1.011 / 1.002 to 1.028 / 1.021, still invisible and still more even than v0.1, and the 4000 K mix stays
within du'v' 0.0003 of its average over the visible wall. About 61 % of the LED flux leaves through the PLA (v0.1
~55 %; 20 % wall transmission assumed, VERIFY O2), so ~37 lm at 4000 K full. The visible wall is θ > 50° from the
bottom pole; seen from below, the 45° collar band (θ 30–45°) reads darker by design (B8). The opening is as wide
as the board (r 9.0) with a 0.6 mm vertical bore under it, so no LED ray that can pass the opening is clipped
(moon_shell B14 checks this with cone probes).

## 6. Mechanics of the slim head

- **Inside-stem cup** (`moon_base.py`): Ø20.8 mm PETG cup with the board pocket (Ø18.4), a ledge from r 8.35 under
  the board's clamp band, 4.5 mm free height above the nut for the wires, hex nut socket on a solid floor. Round 3:
  the floor is jammed between that nut and a washer + second nut underneath (the gooseneck end has no shoulder, so
  one nut held nothing), and the thread needs ≥ 9 mm (VERIFY M1).
- **Bayonet turned inside out**: three 3 mm lugs on the cup's outside (45° top and bottom faces, no supports) lock into
  grooves inside the moon's skirt; the groove roof follows the moon's 45° clamp cone and its floor rises over the turn.
  Round 3: the moon turns **clockwise** seen from the top to lock (jar-lid habit, and it tightens the thread), and a
  0.3 mm chamfer leads the skirt onto the cup.
- **The clamp is a designed spring** (round 3, R3-M1): the cup's land sits 0.4 mm under the board top, so the ring's
  overhang rolls down about the board's top edge when the moon's cone presses its chamfer: 0.23–0.39 mm of travel at
  the cone for a 0.9–1.1 mm board. The locked groove floor stands `LOCK_OFFSET` 0.15 mm above the lug's underside,
  preloading the ring by 0.05–0.25 mm. Before, the lock was line-to-line, so the fit was set by print effects (bind
  or rattle). Claims in moon_base B17 and moon_shell B18 check the closure for the board's ±0.1 mm.
- **Clamp ring** (`moon_ring.py`): PETG 0.8 mm (was 0.6), ID 16.4 (round 3: 0.4 mm clear of the LEDs), OD 19.8,
  0.4 mm × 45° chamfer that the moon's cone presses, printed at 0.12 mm layers. The PLA still never touches the board.
- **Coupons**: `coupon_bayonet_cup` (PETG, the real cup's top, cut on one of its layer boundaries) and
  `coupon_bayonet_skirt` (the moon's PLA and process, built from the moon's own profile), tested with 0.9 / 1.0 /
  1.1 mm discs; `LOCK_OFFSET` is the knob (VERIFY M4). **Jig** (`jig_led_board.py`) resized for the 18 mm board.
- All parts PASS the pipeline; `print/` regenerated. Moon placement in the renders follows `moon_z0`.

## 7. What it does to the light

- **Whites unchanged**: same eight LEDs at the same 25 mA, 34–61 lm of LED flux.
- **Colour and night modes about half as bright** with one RGB instead of two: red night 1.1 lm (was 2.1), soft orange
  1.5 lm (~3), candle 2.4 lm (~5), 6500 K 30 lm (40; blue now sets its limit). Green and Blue are unchanged (3.7 and
  0.9 lm):
  v0.1 ran two LEDs at half current, v0.2 one at full.
- **Low battery**: below ~3.7 V (typical dies; a high-V_F die never fully regulates, R3-E3) the green and blue
  channels fall out of regulation (the LP5012 has no per-channel
  current step to run them at 12.5 mA as v0.1 did). Green and Blue modes dim gracefully; the small G/B share of the
  mixed whites drifts slightly warm in the last ~30 % of the charge. Option if it shows: R1 3.65 kΩ (20 mA on every
  channel, −20 % white) in the next revision. VERIFY E9.
- **Runtime improves** with the driver's lower supply current: ~6.5 h at 4000 K full (was ~5.5 h), ~45 h soft white at
  level 10, ~100–150 h red night light (was ~40 h; the range is the datasheet's 4–6 mA vs 10 mA typical, VERIFY E7). (v0.1's table put level 10 at 25 % of full; the level table gives 16 %.)
- **Thermal**: the same three layers (firmware derating, current caps, hardware thermostat). The board is smaller, so
  it runs warmer per watt; derating and the 110 mA cap are unchanged and VERIFY T2–T4 and T6 cover the bench check.

## 8. Cost and build

- Parts for two lamps: Farnell £39.28 ex VAT (was £44.53) + DigiKey UK LP5012 £2.70, which adds ~£12 shipping unless
  the basket reaches DigiKey's free-delivery threshold. Net about the same, or ~£7 more.
- Assembly: the WQFN and 0402s need a stencil and a hot plate (or hot air) on the LED board's bottom face. The
  recommendation is now JLCPCB Economic assembly of that face only (~£10–25 for five boards) and hand-fitting the top
  (eight 2835s, one PLCC-4, one 0402). `bom/assembly_routes.md`.

## 9. New or changed VERIFY items

E7 (LP5012 + MCP9800 supply current), E8 (channel current with R1 2.94 kΩ), E9 (G/B regulation as the battery
falls), E16 (joints: diode test from each LED's exposed cathode pad end, then first light and the DEVICE_CONFIG1
read-back), E17 (thermostat path at room temperature with the `bench_tstat_low` build), E18 (VCAP ripple and IREF
ground, round 3), T1 (mode currents, 4000 K full ≈ 178 mA), T3 (TC2 on U1, frozen-code log), T6 (hot-air thermostat
trip and re-init), O2 (total flux ≈ 37 lm), O4 (uniformity photos against 1.028 / 1.021 / 1.037), O5 (flicker: 29 kHz
PWM, dither and brightness-register steps), M1 (thread length ≥ 9 mm for the jam nut), M4 (bayonet coupons in PETG +
PLA with 0.9 / 1.0 / 1.1 mm discs; tune `LOCK_OFFSET`), M5 (ring preload). Details:
`docs/verification/VERIFY.md`.
