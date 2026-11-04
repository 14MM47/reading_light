# Round 3: documentation consistency (LED board v0.2, slim moon head)

Adversarial reviewer, 2026-11-03, against repo HEAD `0fbb5b4`. Scope: the human-facing documents against the
sources of truth (design.py / parts.py / fab outputs / reports; gen_modes.py / modes_table.h / board_map.h / config.h /
main.cpp / lightcore; moonlib.py and the parts / print/README.md; build_bom.py / ORDER.md; head_v02.py / .txt).

Method: read every listed document line by line. Ran `python3 firmware/tools/gen_modes.py` (its summary matches;
modes_table.h was rewritten byte-identical). Computed the moonlib-derived dimensions. Read the DRC/ERC JSON, the
bottom-paste Gerber (the EP is split into 4 windows) and the J1/U2/R2 pad positions through pcbnew. Checked the quoted
datasheet facts against the SLVSEH2B (LP5012) and DS21909D (MCP980x) text. Checked that every referenced path and
VERIFY ID exists. No repo file was edited except this report.

## Summary

**3 MAJOR, 16 MINOR, 13 NOTE.** The v0.2 numbers mostly agree across the documents. These all match the sources:
board size, rules, finish and stencils; part references and values; I²C addresses; channel current; PWM; mode flux;
thermal thresholds; head dimensions; optics; the Farnell/DigiKey totals; the D1–D9 W/C assignment.

The three MAJOR items each lead a builder to the wrong thing:
- The committed `deliverable/` is still the v0.1 pack (LED board v0.1 Gerbers, pre-LP5012 firmware), and README and
  PLAN point to it as done.
- `bom/ORDER.md` recommends bare LED boards. Every other document recommends fab assembly of the WQFN side.
- Handoff 02's substitution rule allows 0603 resistors on lines that are 0402 on the LED board.

The MINOR items are stale numbers and procedures, mainly:
- a wrong VERIFY ID in gen_modes.py;
- an E17 thermostat test that the firmware cannot do as written;
- the 0.6 mm ring still named in two part requirement lines;
- stale optics comments in moonlib.py;
- a wrong v0.1 price;
- a wrong "no drop-in" claim for the MCP9800.

### Checked and consistent (no finding)
- **Board.** Ø18.0 mm, 1.0 mm, 2 layers, 1 oz, ENIG, white mask / black silk, 0.15 / 0.15 mm, vias 0.6 / 0.3 mm
  tented, stencils 0.12 top / 0.10 bottom, qty 5. The same in design.py:200-214, FAB_NOTES.md, handoff 01:45-54,
  handoff 05:9, PLAN.md:55 and led-board-v0.2.md §1/§4. ERC 0, DRC 0, 0 unconnected, 0 parity (reports/*.json; the
  main board has 2 silk warnings only).
- **Parts.** U1 LP5012 (16 VCC, 17 SDA, 18 SCL, 19 EN, 20 IREF, 1 VCAP, 14/15 ADDR to GND), U2 MCP9800A0 (1 VDD,
  2 GND, 3 ALERT, 4 SCL, 5 SDA), R1 2.94k, R2 2.4k on top in the NE (D1/D2) gap, C1/C4 1 µF, C2 10 µF 0603, C3 100 nF.
  D1/3/5/7 = W 2700 K and D2/4/6/8 = C 5000 K, D9 the RGB. The BOMs, CPL, handoffs 01/05, FAB_NOTES, the design note
  and the deliverable templates all agree.
- **J1.** Pins 1 GND, 2 VLED, 3 SCL, 4 SDA. The silk reads G NW, V SW, C NE, D SE (top view), so the wire order
  G V D C = J3 pins 1–4. The Qwiic colours match everywhere.
- **I²C and driver.** 0x14 / 0x48 (config.h:9-10 and all docs). 25.0 mA = 105 × 0.7 / 2.94k. 29 kHz, 12-bit
  (9 + 3 dither). DEVICE_CONFIG1 = 0x1C. CONFIG 0x68. TSET 60 / THYST 52; POR defaults 80 / 75.
- **Thermal.** Derating 45 / 52 / 58 °C, caps 200 / 110 mA, 30 % fail-safe after 3 s, frozen-sensor time 5 min
  (lightcore.h:21-30). The same in PLAN, electronics.md §2 and VERIFY T5a/T5b.
- **Light.** Mode flux 34.0 / 40.9 / 61.2 / 37.2 / 30.1 / 2.4 / 1.5 / 1.1 / 3.7 / 0.9 lm. 4000 K full = 177.5 mA.
  Runtimes ~6.5 h / ~45 h / ~150 h. Level 10 = 16 %.
- **Head.** Cup Ø20.8, lugs Ø22.4, skirt Ø25.3 (12.65 r), skirt ID 21.1, pocket Ø18.4, ring 0.8 / 16.0 / 19.8 with a
  0.4 chamfer, opening r 9.0 (23.69°), LED depth 1.2 (board top 1.9 below the cut), bore 0.60 mm, ledge r 8.35,
  30° twist, cam 0.25, ~7 % of the sphere (30.4°). print/README sizes agree.
- **Optics.** 1.011 / 1.002 / 1.037; v0.1 1.068 / 1.063 / 1.054; escape 0.636 (39 lm = 61 × 0.636). head_v02.txt =
  PLAN = design note = VERIFY O2/O4 = moon_shell B13.
- **Money.** Farnell £39.28 ex VAT (£47.14 inc), DigiKey £2.70 (£3.24) + ~£12, 31 Quick Paste lines. ORDER.md =
  assembly_routes = design note (apart from R3-D4).

## Findings

| ID | Sev | Location | Says vs source | Corrected text |
|---|---|---|---|---|
| R3-D1 | MAJOR | README.md:14; PLAN.md:4, :181 | Both send the builder to `deliverable/` ("Everything to build it"; status "done"). The pack comes from commit 5374af2 (deliverable/MANIFEST.txt:1-2, "v0.1"). `01-pcb-manufacture/led-board/led-board-v0.1-gerbers.zip` is the never-ordered Ø26 TLC59116 board, and its hex files predate the LP5012 firmware. Source: hardware/led-board/design.py:33 REV "0.2", fab/led-board/v0.2/. The generator was updated in 0fbb5b4 but has not been run. | Regenerate (`PIO=… python3 tools/build_deliverable.py`) once round 3's reports exist, then commit. Until then, the status cell at PLAN.md:181 should read "**stale (v0.1 LED board): regenerate after round 3**". PLAN.md:4 should read "The build pack in `deliverable/` is being regenerated for LED board v0.2; until then use `fab/`, `print/` and `bom/` directly." |
| R3-D2 | MAJOR | bom/ORDER.md:86, :90 (bom/build_bom.py:192, :196) | Says "Recommended route 1: 5 main + 5 LED bare boards with stencils" and "Total for this build (route 1)". But assembly_routes.md:36, handoff 01:56-58, PLAN.md:37 (R21) and led-board-v0.2.md:144-146 all recommend JLCPCB Economic assembly of the LED board's bottom face, and handoff 02:6 says to read ORDER.md first. | build_bom.py:192: "Recommended: the main board as bare boards + stencil (PCBWay ≈ £40–60 incl. shipping, or JLCPCB ≈ £15–35); LED board v0.2 with JLCPCB Economic assembly of its bottom face (U1, U2, R1, C1–C4; ≈ £10–25 + extended-part fees) unless you already do QFNs (`bom/assembly_routes.md`). Upload …". build_bom.py:196: "## 5. Total for this build (bare boards; add ≈ £10–25 for the LED board's bottom-side assembly)". Then regenerate ORDER.md. |
| R3-D3 | MAJOR | docs/handoffs/02-parts-order.md:9-10 | Says an out-of-stock "(search MPN)" line takes "any 0603 1 % thick-film resistor of the same value". The LED board's two search-MPN resistors are 0402: ORDER.md:38 RC0402FR-072K94L and :42 RC0402FR-072K4L (parts.py:109-112; R_0402_1005Metric in fab/led-board/v0.2/bom_jlcpcb.csv:6, :10). A 0603 R1 or R2 does not fit the 0402 lands. | "choose the exact MPN; if it is out of stock, any 1 % thick-film resistor of the same value **and the same case size** (0603 for the main board, **0402** for the LED board's RC0402 lines), or an X5R/X7R ceramic of the same value, voltage ≥ listed and the same case size, is fine." |
| R3-D4 | MINOR | docs/design/led-board-v0.2.md:142 | Says "Farnell £39.28 ex VAT (was £44.03)". The v0.1 basket was £44.53 (`git show 3d31105:bom/ORDER.md`: "Farnell subtotal ≈ £44.53"). The "~£7 more" that follows only works out with £44.53. | "Farnell £39.28 ex VAT (was £44.53)" |
| R3-D5 | MINOR | led-board-v0.2.md:32 | Says "4–6 mA supply current instead of 25–37 mA". KEYSPECS.md:261 gives 29 mA max at 720 Ω; 37 mA is the 180 Ω row (already corrected in round2 electrical_firmware.md #57). The same note at :18, and electronics.md:74, say "up to 29 mA". | "4–6 mA supply current instead of up to 29 mA (TLC59116 ICC max at REXT 720 Ω)" |
| R3-D6 | MINOR | led-board-v0.2.md:151 | Says "E16 (WQFN joints: every LED from its cathode via …)". The vias are tented on both sides (fab/led-board/v0.2/FAB_NOTES.md:7), and VERIFY.md:42 and handoff 05:59-60 probe the exposed inner end of the cathode pad. | "E16 (WQFN joints: diode-test every LED from the exposed inner end of its cathode pad, because the vias are tented, then the DEVICE_CONFIG1 read-back)" |
| R3-D7 | MINOR | led-board-v0.2.md:137-138 | Says the board "runs warmer per watt; derating and the 110 mA cap are unchanged and VERIFY T1/T6 cover the bench check". T1 measures mode currents only (VERIFY.md:49). The board-to-PLA offset and the PLA limits are T2–T4 (VERIFY.md:50-52). | "… are unchanged; VERIFY T2–T4 (board-to-PLA offset, PLA temperatures) and T6 (thermostat) cover the bench check." |
| R3-D8 | MINOR | firmware/tools/gen_modes.py:9, :101; VERIFY.md:35 | gen_modes cites "docs/verification/VERIFY.md M1" and "VERIFY M1" for the G/B headroom. VERIFY M1 is the gooseneck thread (VERIFY.md:74); the G/B item is E9 (VERIFY.md:35). E9's own tag "(M1, F10; v0.2)" means round 1's M1/F10, which invites the mix-up. | gen_modes.py:9: "(supply headroom: docs/verification/VERIFY.md E9)". gen_modes.py:101: "(VERIFY E9)". VERIFY.md:35: "G/B regulation (round1 M1, F10; v0.2)". These are comments only, so modes_table.h does not change. |
| R3-D9 | MINOR | VERIFY.md:33 (E7) | Pass (a) is "≤ 0.3 mA (LP5012 ≤ 10 µA + MCP9800 ≤ 0.2 mA + …)". The MCP9800 draws 200 µA typ / 400 µA max while converting (KEYSPECS.md:421; DS21909D p.1), and the firmware never shuts it down, so an in-spec sensor can fail E7. | "(a) ≤ 0.45 mA (LP5012 ≤ 10 µA + MCP9800 0.2 mA typ / 0.4 mA max, converting continuously)" |
| R3-D10 | MINOR | VERIFY.md:26 (F5) | The If-not column says "Debug log: `lp_ok` / LP5012 DEVICE_CONFIG0 (Chip_EN)". The debug line prints `T= V= mode= lvl= cap= lp= ts=` (firmware/src/main.cpp:300-305), and `lp=` is DEVICE_CONFIG1. Neither `lp_ok` nor CONFIG0 is printed. | "Debug log: `lp=` returns to `1C` within ~3 s (`--` = LP5012 not answering: check the cable, VLED, U1); `ts=1` once the thermostat is re-armed" |
| R3-D11 | MINOR | VERIFY.md:43 (E17) | Says "Debug build: write TSET 30 °C to the MCP9800". No build or command can do this: the firmware has no serial input. Its 10 s read-back rewrites TSET/THYST from config.h (main.cpp:121-133, :294-296). With THYST still 52 > TSET 30 the comparator band is inverted, and the 4-fail power-cycle (main.cpp:320, `last_temp_c < THYST`) fires every 2 s. | "How: temporarily set `TSENSE_TSET_C 30` and `TSENSE_THYST_C 28` in `config.h`, flash `-e attiny3216_debug`, and warm U2 with a finger. Pass: ALERT pulls EN low, all LEDs go off, `lp=--`; the light returns once U2 cools below 28 °C. Restore 60 / 52 and reflash the release build." |
| R3-D12 | MINOR | handoff 02:12-14 | Says "the MCP9801–03 are 8-pin, a different footprint; there is no drop-in". DS21909D's ordering information lists the MCP9802A0T-M/OT in SOT-23-5 with the same pinout and address (only the 01/03 are MSOP/SOIC-8); KEYSPECS.md:419 notes that the 02 adds a bus time-out. | "(the MCP9801/03 are 8-pin, a different footprint; the **MCP9802A0T-M/OT** is the same SOT-23-5 part plus an SMBus time-out and drops in). Nothing from another maker fits this footprint." |
| R3-D13 | MINOR | bom/assembly_routes.md:30 | Says "Order 5 boards and enough parts for 3–4 attempts (the BOM spares cover this)". The 2-lamp BOM buys LP5012 ×3 (ORDER.md:53), RGB ×3 (:37) and 10 + 10 whites (:35-36, of which 8 + 8 are needed). That is one spare bottom side, or two complete boards plus 2 spare whites per CCT. | "Order 5 boards. The BOM's spares cover one extra LED-board bottom side (3 LP5012, 3 RGB); for more attempts add LP5012s to the DigiKey line (one order, one delivery charge)." |
| R3-D14 | MINOR | cad/parts/moon_shell.py:18 (B12); cad/parts/moon_base.py:9 (B9) | Both still say "a 0.6 mm PETG ring". Source: moonlib.py:40 RING_T = 0.8 and moon_ring.py:7-8 B3; moon_ring's own B1 is already marked superseded. | moon_shell B12: "… the PLA moon never touches the LED board: a PETG ring sits between them (0.6 mm in v0.1; 0.8 mm in v0.2, moon_ring B3)". moon_base B9: "a PETG clamp ring (moon_ring.py; 0.8 mm in v0.2) sits between …" |
| R3-D15 | MINOR | cad/parts/_lib/moonlib.py:27, :30, :31-32, :64 | :27 cites `docs/design/optics.md`, which does not exist. :30 says Z_CUT is "~ -20.81"; it computes to -20.51. :31-32 say "max/min ~1.05 … (1.0 -> 1.03, 2.0 -> 1.12)"; head_v02.txt:2-5 gives 1.011 at 1.2, 1.012 at 1.0 and 1.055 at 2.0. :64 says R_RIDGE is "~ (8.39, Z_CUT + 0.03): a 67 deg ridge"; it computes to (8.56, Z_CUT − 0.17), inside the r 9.0 bore, so it is not on the part, and it contradicts :29 ("not a 67 deg knife edge"). | :27: "(docs/design/optics/head_v02.py, corrected model of 2026-11-03)". :30: "(~ -20.51)". :31-32: "max/min 1.011 one white, 1.002 all whites, 1.037 RGB on the visible wall (1.0 -> 1.012, 2.0 -> 1.055; head_v02.txt)". :64: "~ (8.56, Z_CUT - 0.17): the cone/sphere intersection, inside the r 9.0 bore, so not on the part (coupon_bayonet uses it only to size its cap)". |
| R3-D16 | MINOR | hardware/parts.py:50-51, which feeds bom/BOM.csv:31, fab/led-board/v0.2/bom_pcbway.csv:9 and bom/farnell_order.csv:30 | Gives the MCP9800 as "+/-1 C typ / +/-3 C max". DS21909D p.1 and KEYSPECS.md:422 give ±0.5 °C typ at 25 °C and ±1 °C max over −10…+85 °C; ±3 °C max is the −55…+125 °C figure. led-board-v0.2.md:55 has it right. | "+/-0.5 C typ, +/-1 C max (-10 to +85 C)". Then rebuild the BOM and the LED-board fab files. |
| R3-D17 | MINOR | PLAN.md:81-82 | Says "the colour and night modes give about half the v0.1 flux (red night 1.1 lm, candle 2.4 lm, 6500 K 30 lm)". But 6500 K is 30 against 40 lm, i.e. 75 % (led-board-v0.2.md:128, electronics.md:76; gen_modes COOL_6500 30.1 lm). | "… give about half the v0.1 flux (red night 1.1 lm, candle 2.4 lm), and 6500 K falls from 40 to 30 lm (blue sets its limit); Green and Blue are unchanged …" |
| R3-D18 | MINOR | handoff 05:40 | Says "pin-1 dot to the silk dot". U1's B.SilkS pin-1 mark is a filled triangle beside pin 1 (the KiCad Texas_RUK0020B footprint's fp_poly in led-board.kicad_pcb); there is no silk dot. | "pin-1 dot on the package to the silk triangle beside pin 1" |
| R3-D19 | MINOR | handoff 01:11; PLAN.md:3, :179 | These cite `docs/verification/round3.md` and say "rounds 1–3 done". Neither that file nor round3/electrical_firmware.md and mechanical_optics.md exists yet, and tools/build_deliverable.py:284-289 exits on a missing source. | Write round3.md and both reports before regenerating. Until then PLAN.md:179 should read "rounds 1–2 done, round 3 in progress". |
| R3-D20 | NOTE | docs/datasheets/KEYSPECS.md:3, :405 | :3 gives "Folder: `/tmp/claude-0/…/scratchpad/ds/`". That is a cloud-session scratch path, not in the repo, so Matt cannot open the PDFs the page references point to. :405 says "First I2C access ≤ 500 µs after the EN rising edge (tEN_H)", which reads as a deadline. SLVSEH2B §7.6 gives 500 µs as the maximum time before the device accepts I²C; main.cpp:48 says "> 500 us" and waits 10 ms (:199). | :3: "The datasheet PDFs were read in the cloud session and are not in the repo; fetch them from each part's URL." :405: "Wait ≥ 500 µs after the EN rising edge before the first I²C access (tEN_H, max)." |
| R3-D21 | NOTE | hardware/led-board/design.py:166 | Says "the wires go by the G V C D silk". :170, FAB_NOTES.md:11, led-board-v0.2.md:81 and the handoffs all say "G V D C" (the J3 pin order). The silk is one letter per pad (design.py:388). | "… the wires go by the G / V / D / C silk letters beside the pads" |
| R3-D22 | NOTE | firmware/include/modes_table.h:15 (generated by gen_modes.py:87) | The Daylight 5000K comment says "WW+CW+G, Duv 0 by construction", but the recipe is {0, 4096, 0, 0, 0}: CW only. gen_modes builds the note from the group set it tried, not the groups in use. | In gen_modes.py:87, build the note from the groups with non-zero drive (that gives "CW only"), then regenerate. |
| R3-D23 | NOTE | PLAN.md:164; electronics.md:69; led-board-v0.2.md:132 | Give the TLC59116's G/B current step as "12.5 mA". gen_modes.py:100 and round1.md:102 (F9: CG steps 8.3 / 12.4 / 24.8 mA) give 12.4 mA. History only. | "12.4 mA" in all three. |
| R3-D24 | NOTE | PLAN.md:64; VERIFY.md:64 (O3); tools/build_deliverable.py:378, :380 | "v0.2 option" (the reading LED, the NTC charger) now reads as part of the LED board v0.2 being built. | "next-revision option" |
| R3-D25 | NOTE | hardware/parts.py:101 | R_2K4 0603, "LED board RESET_N pull-up": no board uses it (it appears only in main-board/design.py:42 LIB). The v0.2 EN pull-up is R_2K4_0402 (parts.py:111). | Delete the entry and its LIB key, or mark it unused. |
| R3-D26 | NOTE | bom/ORDER.md:82 (build_bom.py:74) | Says "Stencils … for both boards £10". There are now three stencils (main top, LED top, LED bottom 0.10 mm), and assembly_routes.md:11 puts them at ~£16–24 (PCBWay) or ~£5–8 (JLCPCB). | TOOLS item: "Stencils (frameless): main top 0.12, LED top 0.12 + bottom 0.10 mm", price "≈ £5–24 (JLCPCB / PCBWay)" |
| R3-D27 | NOTE | PLAN.md:100; electronics.md:28, :45; main-board/design.py:116 | The decision log says "10 µF capacitors are 0805 16 V", yet LED-board C2 is 0603 10 V (parts.py:117) and no exception is recorded. "LED board's ~9 µF" is the v0.1 figure; v0.2 VLED has C1 1 µ + C2 10 µ + C3 0.1 µ nominal, less under 4 V bias. | Add to the 2026-11-03 log: "LED-board C2 is 0603 10 V (VLED ≤ 4.2 V, bulk only)". Recheck the ~9 µF figure (and the C8 dV/dt sizing) against v0.2. |
| R3-D28 | NOTE | PLAN.md:35 (R19) | Says "Flicker-free (PWM ≥ 20 kHz)". v0.2 adds the LP5012's dither cycle at fPWM/8 ≈ 3.6 kHz (2.6 kHz at the 21 kHz minimum; KEYSPECS.md:400), and only VERIFY O5 accepts it (VERIFY.md:66). | Add to R19 or the 2026-11-03 log: "LP5012: 29 kHz PWM (21 kHz min) with a 3-bit dither cycle at ≈ 3.6 kHz; turn dithering off (9-bit) if O5 shows it." |
| R3-D29 | NOTE | hardware/led-board/design.py:38 | Says "bodies and pads stay inside this radius" (7.8). The 2835 anode pad (LED_PLCC_2835_Dense pad 2: x 0.75–2.0, y ±1.1) reaches r 7.88 at its outer corners. That is still inside the r 8.0 copper limit, so only the comment is wrong. | "bodies stay inside this radius (pads reach r 7.88, inside the r 8.0 copper limit)" |
| R3-D30 | NOTE | PLAN.md:50, :148; led-board-v0.2.md:16 | "on a 5.8 mm ring" means the radius (design.py:37 RING_R = 5.8) but reads as a diameter. | "on an r 5.8 mm ring" |
| R3-D31 | NOTE | handoff 01:58 | Says "… then hand-fit the top (`bom/assembly_routes.md`, recommended). If Matt prefers assembly instead: upload …". After a sentence that recommends assembly, "instead" reads as the opposite. | "For fab assembly (recommended for the LED board's bottom face): upload …" |
| R3-D32 | NOTE | README.md:5 | Says "tunable CRI-97 whites from 1900 K candle to 6500 K". The candle (WW + R + G) and 6500 K (CW + B + G) modes are RGB mixes (modes_table.h:16-17), not CRI-97 whites. | "CRI-97 whites from 2700 K to 5000 K, plus a 1900 K candle and a 6500 K blue-white mixed with the RGB LED" |

Legitimate history was left alone: the PLAN decision log 2026-11-02 (TLC59116, Ø26, two RGB, LM75BDP, "25–37 mA"),
round1/round2 reports, the "was" columns in led-board-v0.2.md §1/§5, parts.py:43/:52 comments, superseded B-lines
(moon_shell B4/B7, moon_base B3/B5, moon_ring B1), and "fab/led-board/v0.1/ removed".

## tools/build_deliverable.py (lower priority; committed 0fbb5b4 is mostly v0.2 already)

1. **:377.** "See `00-overview/open-decisions-and-round1-summary.pdf` §5" points at round1.md:107-120. That section
   holds the four v0.1 decisions (including "The LED board has 2 spare TLC outputs"); the template's items 4 (LP5012
   G/B drift) and 5 (WQFN assembly) are not in it. Point at round3.md's decisions section (and render round3.md
   into `00-overview/`), or at led-board-v0.2.md §7–8.
2. **:378, :380.** "v0.2 option" → "next-revision option" (R3-D24).
3. **:284-289, :535.** These require round3.md plus round3/{electrical_firmware, mechanical_optics,
   docs_consistency}.md. "the nine full reviewer reports" is only true if all three round-3 reports exist under
   those names.
4. **:348.** "has been through three verification rounds" is only true once round3.md exists (R3-D19).
5. **:428/:446.** readme_parts copies ORDER.md's last line, which is the route-1 (bare boards) total. Fix R3-D2
   first, or label it "bare-board route".
6. **:372 and the status tables need no change.** The main board has 2 silk warnings and the LED board has none
   (hardware/*/reports/drc.json).
