# Verification round 2: re-check of the round-1 fixes, fab package and fit

Date 2026-11-02. Two independent reviewers worked on the committed state after round 1. Neither edited the repo.
Full reports:

| Reviewer | Brief | Report |
|---|---|---|
| Electrical + firmware | confirm every round-1 fix against the datasheets and the netlists, and hunt for problems the fixes introduced | [round2/electrical_firmware.md](round2/electrical_firmware.md) |
| DFM + fit (adversarial) | Gerbers, drill, BOM/CPL and land patterns against PCBWay; board-to-enclosure fit; hand assembly | [round2/dfm_fit.md](round2/dfm_fit.md) |

**Result:** 3 blockers and 4 majors raised, all fixed. Every round-1 electrical and firmware fix was confirmed in
place and wired correctly: design.py, a fresh netlist and the PCB pad nets agree (0 mismatches). The blockers were
in **mechanical integration**, which neither ERC/DRC nor the per-part CAD checks could see, because each part was
checked only against its own context. Two process gaps closed as a result: cross-part claims (B5 in `pack_back`,
B10/B11 in `moon_base`, B4 in `button_caps`), and IREF step selection moved into the host-tested core.

## Electrical + firmware

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| R2-E1 | MAJOR | Q4 switched hard: charging the LED board's ~9 µF from VSYS gave multi-amp peaks and dipped VSYS (the MCU supply) to ~2.0–2.4 V at every LED-board power-on, wake and hot-plug | **FIXED.** R13 10 k from PB2 to the gate and C8 100 nF gate–drain give a ~2.5 V/ms ramp and ~25 mA charging current. Bench check VERIFY E13 (scope VSYS and VLED) |
| R2-E2 | MINOR | Q4 power-cycle likely no TLC POR (VLED has no discharge path) | **FIXED** (firmware). Sends TLC SWRST (0x6B: A5h 5Ah) first, then cuts power with SDA/SCL driven low, so VLED bleeds through the pull-ups (τ ≈ 16 ms, 200 ms off) |
| R2-E3 | MINOR | PTC hold margin thin when warm (0.51 A worst case vs 0.55–0.60 A hold at 50–60 °C) | **FIXED.** F1 is now MF-MSMF110/16X-2 (1.1 A hold, 16 V, 0.06–0.20 Ω), same 1812 footprint. VERIFY E14 |
| R2-E4 | MINOR | "TVS conducts and trips the PTC" is not sound; 6.4–7.5 V sources pass | **ACCEPTED, docs corrected.** This is not over-voltage protection; real OVP (eFuse) is on the v0.2 list (electronics.md §1) |
| R2-E5 | MINOR | TLC RESET became a 10 k node near the metal neck | **MITIGATED.** R2 is now 2.4 k (~4× stiffer). A 1–10 nF filter cap was tried and made the 26 mm board unroutable, so it is on the v0.2 list |
| R2-E6..E10 | NOTE | VREF through 1 k with programmers; USB-unplug handover; F1 voltage drop; no VLED test pad; generic 1812 land | Handoff 04 recommends SerialUPDI and flashing on battery. E7/E8 → VERIFY E12/E15. **TP7 VLED added.** F1 land **ACCEPTED** (the KiCad 1812 land fits the Bourns Style 1 body) |
| R2-F1 | MINOR | Green/Blue at level 15 still picked the 25 mA step (drive 0.500 vs raw gain 0.4961) | **FIXED.** Step choice is `cg_select()` in the core: it compares in drive units with tolerance, and the recipes use 0.496. New host tests: never clips, lowest fitting step, G/B never at 25 mA, hysteresis |
| R2-F2 | MINOR | Cap changes stepped with no fade; the frozen timer used stale timestamps | **FIXED.** Trust changes call `retarget()` (160 ms fade). The frozen timer runs from the later of "reading changed" and "load started". Two new tests |
| R2-F3 | NOTE | First temperature read after a power-cycle can precede the LM75B's first conversion | **FIXED.** Reads are ignored for 300 ms after the LED board powers up |
| R2-F4 | NOTE | IREF step choice not host-tested | **FIXED** (as F1) |
| R2-F5 | NOTE | LM75B Conf/Tos never read back | **FIXED.** Read back every 10 s and re-armed if it differs |
| R2-F6..F9 | NOTE | Comment on TLC bus time-out; BOD text; 200 mA cap never binds (max mode 177.5 mA); missing doc reference | **FIXED** (comments, handoff 04, electronics.md, lightcore.h) |
| §3 | NOTE | 12 stale statements in electronics.md | **FIXED** (all 12) |

## DFM + fit

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| R2-D1 | BLOCKER | The 3.0 × 2.8 mm lead slot could not pass the cell's pre-fitted PHR-2 plug (5.8 × 4.5) | **FIXED.** Slot 6.4 × 5.0 mm (x 10.0–16.4, y 49.4–54.4) under the mated plug, with 0.35 mm to the USB-C shell pad. Handoff 05 §4.2 |
| R2-D2 | BLOCKER | `pack_back` locators reached 1.05 mm into the shell's side walls and 0.4 mm into the bottom wall | **FIXED.** Locators derived from the cavity; the walls locate the sides and bottom. New claims check the plate stays inside the cavity |
| R2-D3 | BLOCKER | Gooseneck thread end could hit U1 (1.0 mm gap), and the wires had no room to turn | **FIXED.** 4.5 mm under the board (`UNDER_BOARD_DEPTH`, claim B10); the useless nut-level notch is removed. VERIFY M12: file the thread flush. Kapton disc on U1 (handoff 05) |
| R2-D4 | MAJOR | RGB polarity instructions wrong (the package mark is pin 3, not pin 1) | **FIXED.** Handoff 05, the per-part BOM notes and FAB_NOTES now say: package mark on the silk chamfer, pin 1 = common anode on the "1" |
| R2-D5 | MAJOR | J2 header is 5.5 mm tall vs 5.6 mm headroom | **FIXED.** 0.8 mm pocket in the face's inner surface over J2 (claim B11), giving 0.9 mm clearance |
| R2-D6 | MAJOR | Slide-switch tip 1.15 mm below the surface; the promised chamfer was missing | **FIXED.** A 45°-tapered 0.9 mm finger recess around the window puts the tip 0.25 mm below the local surface (claim B12). The first try (1.0 mm) failed the 0.84 mm wall check, so the geometry was changed, not the check |
| R2-D7, D8 | MINOR | FAB_NOTES: plated slots and via size wrong | **FIXED** |
| R2-D9 | MINOR | LED CPL listed J1 pads; wrong D2 note; USB-C typed SMD | **FIXED.** The CPL keeps only bought parts, notes are per part type, and USB-C is typed "SMD + THT (shell slots)" |
| R2-D10 | MINOR | Assembly drawings: no values, DNP not crossed out, W/C positions unclear, refs far from parts | **FIXED.** Values on the Fab layer, `--crossout-DNP`, a title block, W/C silk letters by every white LED, and refs placed outward next to their part. The zoomed PNG renders are named in handoff 05 |
| R2-D11 | MINOR | DOWN cap flange 0.2 mm from the H2 boss | **FIXED.** Flange Ø9.0; claim ≥ 0.25 mm with worst-case play (0.30) |
| R2-D12 | MINOR | No support for the second-side stencil/reflow; stencil thickness unspecified | **FIXED.** New printed `jig_led_board`, 0.12 mm stencils in FAB_NOTES, handoff 05 rewritten for it |
| R2-D13 | MINOR | PCM12 rated 255 °C max | **FIXED.** Handoff 05: SW1 fitted by iron after reflow |
| R2-D14 | MINOR | USB-C window chamfers can block square overmolds | **FIXED.** Window 13.4 × 7.6 mm with 0.8 mm chamfers (claim B13); your cables are VERIFY M8 |
| R2-D15 | MINOR | 0.9 mm board could rattle | **FIXED.** Pocket 0.88 mm deep, so the board stands proud and the ring always preloads it (claim B11) |
| R2-D16 | MINOR | Cable anchor step impossible as written | **FIXED.** Service loop, plus silicone at the gooseneck bore entrance |
| R2-D17 | MINOR | STEP missing J1/J2/F1/2835 models (cloud install has no 3D libraries) | **ACCEPTED.** Handoff 01: re-export the STEP locally before fit checks |
| R2-D18 | MINOR | Battery lead path not modelled | **VERIFY M13.** A lead channel is added if the real cell needs one |
| R2-D19, D24 | NOTE | Silk line width at the fab minimum; heavy paste on the 2835 cathode pad | **ACCEPTED** for v0.1 (v0.2: ≥ 0.15 mm silk lines, 80 % paste) |
| R2-D20 | NOTE | Drill maps and empty layers in the zip | **FIXED** (excluded) |
| R2-D21 | NOTE | Plug keep-out allows vias | No action (the slot moved them) |
| R2-D22 | NOTE | Breakaway-tab nubs on the round board | **FIXED** (FAB_NOTES asks for a clean edge) |
| R2-D23 | NOTE | Handoff 01 size text; LED silk without date; job file rev "rev?" | **FIXED** (title block set from the design: rev 0.1, date) |
| R2-D25 | NOTE | Silicone blob could spread onto the ledge | **FIXED** (handoff 05: keep it inside r ≈ 11 mm) |

## Re-check after the fixes

- Both boards regenerated: **ERC 0, DRC 0 errors, 0 unconnected, 0 schematic parity.** The LED board has no
  warnings at all. The main board has two intended silk warnings (the SW1 outline crosses the edge where the knob
  overhangs).
- Firmware: **29/29 host tests**; `attiny3216`, `attiny3216_debug`, `bench_t_nack` and `bench_t_stuck` build
  warning-free in project code.
- `python3 -m pytest tests`: 4/4 (board map, pins, REXT ↔ `I_CHANNEL_MA`, LED group counts).
- CAD: all **11 parts PASS** (the new `jig_led_board` included) and are re-exported to `print/`.
- BOM regenerated: 29 Farnell lines (PTC changed to MF-MSMF110/16X-2; 2.4 k now used on the LED board).
