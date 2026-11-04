# Verification round 3: LED board v0.2, its firmware and the slim moon head

Date 2026-11-04. Three independent reviewers worked on the committed v0.2 state (LED board v0.2 with the TI LP5012,
the firmware layer for it, the inside-stem moon head, and every document). None edited the design. Full reports:

| Reviewer | Brief | Report |
|---|---|---|
| Electrical + firmware | LED board v0.2 against the LP5012 / MCP9800 datasheets; the driver and thermostat firmware | [round3/electrical_firmware.md](round3/electrical_firmware.md) |
| Mechanical, printing, optics | the head's tolerance stack, clamp, bayonet, printability, coupon, assembly; the optics model | [round3/mechanical_optics.md](round3/mechanical_optics.md) |
| Documents (adversarial) | every human-facing document against the sources of truth and each other | [round3/docs_consistency.md](round3/docs_consistency.md) |

**Result:** 7 MAJOR, 25 MINOR and 26 NOTE findings, none of them a blocker.
- **Electrical/firmware: 0 major.** The circuit is correct against both datasheets.
- **Mechanical: 4 major.** The bayonet gave no designed preload. VERIFY M4 named the wrong tuning knob. The coupon was
  printed in the wrong material. The cup could unscrew from the neck.
- **Documents: 3 major.** The stale deliverable, the order summary recommending the wrong assembly route, and a
  0603 substitution rule for 0402 parts.

All majors are fixed. Fixing them turned up three more defects that the existing checks had passed (see "Found while
fixing"), so the CAD pipeline's wall check is now stricter.

## Electrical + firmware

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| R3-E1 | MINOR | Routed IREF track met U1 pin 20 and R1 pad 1 at their corners: 0.106 / 0.129 mm copper necks, invisible to DRC | **FIXED.** IREF is fixed copper pad centre to pad centre (design.py); a `.kicad_dru` `connection_width ≥ 0.15 mm` rule now runs with DRC (it flags the old joint). Rebuilt: ERC 0, DRC 0 / 0 / 0 |
| R3-E2 | MINOR | C4 (VCAP) and R1 (RIREF) ground returns to the exposed pad run 22–26 mm round the I²C bundle; EP has no vias | **ACCEPTED for this order, Matt to confirm** (decision 3). Both copper layers are full at the board centre (RGB pads, cathode vias, top VLED trunk, D2's cathode pad), so a jumper means re-laying the centre. DC error ~0.2 %. New VERIFY **E18** scopes VCAP and checks the channel current is steady. The doc claims ("at the pin") are corrected |
| R3-E3 | MINOR | G/B headroom stated only for typical dies; a max-V_F die needs ~4.05–4.15 V | **FIXED (docs + test).** electronics.md §2 and the design note give the worst case. **E9** now measures the received dies' V_F first. Remedy if they sit high: R1 3.65 kΩ or a V_F bin |
| R3-E4 | NOTE | LP5012 thermal path: no EP vias; Tj ≲ 90 °C at the 60 °C trip | **ACCEPTED.** T3 puts TC2 directly on U1 and records TC2 − sensor for the T2 re-fit |
| R3-E5 | NOTE | Datasheet also gives 10 mA typ supply (§8.4) | **FIXED (docs).** Supply 4–10 mA, red night ~100–150 h, E7 settles it |
| R3-E6 | NOTE | Würth derating curve not recorded | **FIXED (docs).** KEYSPECS §2 and electronics.md §2; the firmware derating keeps inside it |
| R3-F1 | MINOR | OUTx_COLOR tables contradict the rest of the datasheet; init set Chip_EN before zeroing the outputs | **FIXED.** `lp_init()` configures and zeroes all outputs in STANDBY, Chip_EN last. Contradiction in KEYSPECS; **E8** checks colour 0 and 255 |
| R3-F2 | MINOR | Output registers never read back: a corrupted burst persists | **FIXED.** `lp_verify()` once a second: CONFIG0/1 (re-init on a mismatch) and 07h–16h (full rewrite on a mismatch) |
| R3-F3 | NOTE | Thermostat hold: limits rewritten every 500 ms, `lp_fails` kept counting | **FIXED.** Limits are rewritten only if the read-back differs, and the count is held at 0 while the thermostat holds |
| R3-F4 | NOTE | 0 °C reading accepted after an unplanned LED-board reset | **FIXED.** Every LED-board loss re-arms the 700 ms first-conversion wait |
| R3-F5 | NOTE | Warm restart slewed down from 100 % at 10 %/s | **FIXED.** The first valid reading after init sets the derate at once (still faded). Host test |
| R3-F6 | NOTE | A quiet sensor at equilibrium could lose trust ("breathing" 178 ↔ 110 mA) | **FIXED.** A reading that has risen ≥ 1 °C since the load started keeps its trust; a sensor stuck from the start still loses it after 5 min (T5b). Two host tests; T3 logs `T=` for 15 min |
| R3-F7 | NOTE | Light returns as a step after a re-init | **ACCEPTED** (rare: thermostat release or a cable glitch) |

## Mechanical, printing, optics

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| R3-M1 | MAJOR | The locked bayonet was line-to-line: no designed preload. The only compliance was a 0.08 mm ring roll, so print effects and board tolerance decided between binding (cracking the PLA skirt) and rattling | **FIXED.** The cup's land sits 0.4 mm (`LAND_DROP`) under the board top, so the ring's overhang rolls about the board edge: 0.23–0.39 mm of travel at the cone for a 0.9–1.1 mm board. The locked floor stands `LOCK_OFFSET` 0.15 mm above the lug: 0.05–0.25 mm preload. Claims (moon_base B17, moon_shell B18) check the closure for board ±0.1. `GAP_45` 0.25 → 0.35 keeps the cone and lug tops clear of the lowered moon. Ring printed at 0.12 mm layers |
| R3-M2 | MAJOR | VERIFY M4 named `CAM_DROP`, which does not change the locked fit; the M5 shim adds rigid interference | **FIXED.** M4/M5 tune `LOCK_OFFSET` in 0.05 mm steps; no shims |
| R3-M3 | MAJOR | The bayonet coupon was all PETG; the moon's skirt is PLA at 0.12 mm | **FIXED.** `coupon_bayonet_cup` (PETG 0.16, cut on a real layer boundary) and `coupon_bayonet_skirt` (the moon's PLA, process and slicer overrides, built from the moon's own profile). Tested with 0.9 / 1.0 / 1.1 mm discs |
| R3-M4 | MAJOR | Nothing reacted the captive nut (no shoulder on the gooseneck end), and the moon locked anticlockwise, the thread's loosening direction | **FIXED.** Entry slots moved: the moon locks **clockwise** seen from the top (jar lid; tightens the thread; claim B17). Washer + jam nut under the cup floor (moon_base B16; BOM 2 nuts + a washer); thread ≥ 9 mm (VERIFY M1). Handoff 05: hold the cup band whenever the moon is turned |
| R3-M5 | MINOR | Handoff 05 nut step could not be done as written (socket stops the nut; filing after the cable; heat-shrink above the thread) | **FIXED.** Rewritten: jam nut + washer on, cup screwed on with the socket nut, thread cut before the cable, heat-shrink kept inside the bore at the moon end |
| R3-M6 | MINOR | Ring ID 16.0 could land on the white LEDs' anode solder (0.12 mm margin to pad corners) | **FIXED.** Ring ID 16.4 (claim: ≥ 0.4 mm clear of the LED bodies); design.py comment corrected to pad corners r 7.88 |
| R3-M7 | MINOR | The moon's 82° overhang override also covered the cone, grooves and slots | **FIXED.** Claim B20: everything below the opening plane + 0.6 mm overhangs ≤ 45° (45.01° measured) |
| R3-O1 | MINOR | Optics model left out the RGB package as an occluder | **FIXED.** Added (and the slant-corrected wall area, R3-O2): 1.028 / 1.021 / 1.037 (was 1.011 / 1.002 / 1.037). B21, PLAN, design note, O4 |
| R3-M8 | NOTE | Board not keyed: it can turn with the moon (±30° cable twist per lock) | **ACCEPTED, Matt to confirm** (decision 6). The silicone strain relief takes it |
| R3-M9 | NOTE | No lead-in, no direction cue | **FIXED (lead-in).** 0.3 × 45° skirt chamfer (B19). The cue is now the jar-lid direction; no arrow (it would be an overhang on the cup) |
| R3-M10 | NOTE | Stale comments and requirement text; coupon cap sliver; exploded view drew the nut below the floor; README warnings column | **FIXED**, except the README column: it lists the check's threshold, and the values are in each part's diagnostics |
| R3-O2 | NOTE | Escape fraction ~3 % high | **FIXED.** Slant-corrected area element (flux conservation checked: 1.000 centre source, 0.983 vs analytic 0.9825 under the aperture). Escape 0.61 → ~37 lm (O2) |
| R3-O3 | NOTE | "Visible wall" excludes the underside; the 45° collar reads darker | **ACCEPTED, documented** in O4 and the design note (B8 by design) |

## Documents

All 32 findings were checked against the sources. The three MAJOR ones are fixed:
- **R3-D1.** `deliverable/` was the v0.1 pack. It is regenerated after this round.
- **R3-D2.** ORDER.md recommended bare LED boards. It now recommends JLCPCB assembly of the WQFN face, like every
  other document.
- **R3-D3.** The 0603 substitution rule now says to keep the case size: 0402 on the LED board.

Of the MINOR ones, D4–D18 are fixed:
- the v0.1 basket total;
- the TLC59116 current;
- the E16 probe point;
- the T-items;
- the gen_modes VERIFY reference;
- E7's limit uses the MCP9800's 0.4 mA maximum;
- the F5/E17 procedures. E17 now uses the new `bench_tstat_low` build;
- the MCP9802A0 drop-in;
- the spares claim;
- the 0.6 mm ring lines;
- the moonlib comments;
- the MCP9800 accuracy, which also flows into the BOMs;
- 6500 K at 75 %;
- the U1 silk mark.

D19 (round 3 cited before it existed) is closed by this file.

The NOTE ones D20–D32 are fixed, except D23 (12.4 vs 12.5 mA for the v0.1 G/B step), which is history and left
alone.

## Found while fixing

| What | How it was found | Disposition |
|---|---|---|
| A 0.03 mm lip in the moon where the groove and slot cutters ended inside the clamp cone (roofs 0.03 mm above the cone line) | The new PLA coupon put the moon's own geometry on a small part, where the wall sampler hit it | **FIXED.** Roofs 0.03 mm below the cone line (moonlib `ROOF_C`): the cutter's end is then in the skirt's bore (air) |
| A fold of the moon's inner surface within 1.5° of the north pole (0.009 mm "walls") | Per-facet wall sampling | **FIXED.** The slope limiter let ring-to-ring relief survive to rings ~0.3 mm across; each ring now fades to its own mean from 172° to 176° (the dome-closure bridge zone) |
| The pipeline's wall check sampled facets by area only, so small thin features were almost never sampled; both defects above had passed | The two defects above | **FIXED (check).** Per-facet uniform samples are added (10× the area-weighted count). Unit test `test_wall_check_finds_a_thin_feature_with_little_area` fails on the old check and passes on the new one. All 12 parts re-exported: PASS. Every facet of the head parts' exact geometry was also scanned once: thinnest 1.198 mm (moon, coupon skirt), 0.840 mm (cup) |
| The optics model's first slant correction used a numerical gradient that smeared the 40–50° band's slope onto the first visible ring | The v0.1 rows moved although nothing about them had changed | **FIXED.** Analytic derivative; v0.1 rows back to their values; conservation checked |
| A test read past `OUT_GROUP` (16 outputs assumed, 12 exist) | Writing the new host tests | **FIXED** (`N_OUT`) |

## Re-check after the fixes

- **LED board:** ERC 0, DRC 0 violations / 0 unconnected / 0 parity, with the connection-width rule. The copper is
  unchanged except IREF. The main board is unchanged (v0.1).
- **Firmware:** 32 host tests pass; five AVR builds compile (release, debug, two thermal fault benches,
  `bench_tstat_low`).
- **CAD:** all 12 printable parts PASS the stricter pipeline, including the new claims B16–B21 (moon) and B16–B17
  (cup). `print/`, fitment and assembly renders are regenerated.
- **Docs:** PLAN (decision log 2026-11-04), design note, electronics notes, KEYSPECS, VERIFY (E8, E9, E18, T3, O2,
  O4, M1, M4, M5, M12), handoffs 02–05, BOM (two nuts and a washer per lamp).

## Decisions for Matt

1. **LED board assembly**: hand assembly (stencil + hot plate, only if you already do QFNs) or JLCPCB Economic
   assembly of its bottom face (recommended, ~£10–25), then hand-fit the top. `bom/assembly_routes.md`.
2. **Green/blue headroom**: keep R1 2.94 kΩ (25 mA; G/B dim at low battery, a high-V_F die never fully regulates) or
   3.65 kΩ (20 mA everywhere, −20 % white). Recommended: keep 2.94 kΩ and decide after VERIFY E9 measures the dies.
3. **VCAP/RIREF ground (R3-E2)**: order the board as it is and scope it (E18), or ask for a re-layout of the board
   centre first (EP vias, a GND jumper; about a day of layout and a new review). Recommended: order as is; the
   error is small and E18 catches a problem before the second lamp.
4. **Board keying (R3-M8)**: accept that the board may turn ±30° with the moon (the cable's strain relief takes it),
   or add an edge notch and a key in the cup before ordering. Recommended: accept.
5. Carried over from round 1: reading brightness 20–30 lux (a downward reading LED in the next revision); charging
   without a cell NTC (an NTC charger in the next revision).
