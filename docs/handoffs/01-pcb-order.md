# Handoff 01 — PCB final review and order

**For:** Claude Code in VS Code + KiCad 9 GUI, with Matt. ~45 min. **Matt places the order.**

The boards were generated, routed and checked in the cloud (KiCad 9.0.9, kicad-cli): ERC 0, DRC 0 errors,
0 unconnected, schematic parity clean. That run was after verification round 1; see `docs/verification/round1.md`
for what changed (Q4 LED-board switch, F1 PTC, R3 3.9 k, R5 10 k, R11 VREF, J2 moved with a lead slot, LM75B
thermostat wiring), then round 2 (`docs/verification/round2.md`: battery-lead slot 6.4 × 5.0 mm, Q4 soft turn-on
R13/C8, 1.1 A PTC, VLED test pad TP7, RESET pull-up 2.4 k, W/C silk next to the white LEDs). The LED board was then
redesigned as **v0.2** (2026-11-03, `docs/design/led-board-v0.2.md`): Ø18 mm, TI LP5012 (WQFN-20) + MCP9800A0,
one RGB, 0402 passives, 0.15/0.15 mm rules; round 3 reviewed it (`docs/verification/round3.md`). The fab packages
are ready in `fab/main-board/v0.1/` and `fab/led-board/v0.2/`. The DRC warnings that remain are silk-only, and the
reports list them: the main board's SW1 outline is clipped at the board edge, because the knob overhangs the edge
by design.
This handoff is the human look-over the pcb repo's process requires (steps 3, 4, 6, 7 of its fabrication process),
then ordering.

## 1. Open and inspect (KiCad GUI)
1. `git pull`; open `hardware/main-board/main-board.kicad_pro` and `hardware/led-board/led-board.kicad_pro`.
2. **Do not edit and save the generated files** unless you intend to stop regenerating that board (see CLAUDE.md).
3. Run ERC and DRC in the GUI; expect the same results as `hardware/*/reports/*.json`.
4. Open the 3D viewer (Alt+3) and check:
   * Every part is oriented plausibly.
   * Main board: the USB-C mouth is at the bottom edge, and the slide-switch knob sits past the right edge. The
     JST-SH opening faces the top edge. The JST-PH (battery) opening faces into the board, and the lead slot is
     beside it.
   * LED board: 1.0 mm thick; on top the eight 2835s (cathode pad inward), the RGB at the centre and R2 (0402) in the
     D1/D2 gap; underneath the LP5012 at the centre, the MCP9800 (SOT-23-5), R1/C1–C4 and the G/V/D/C pads.
   * The cloud build had no KiCad 3D models for J1, J2, F1 and the 2835 LEDs, so they are missing from the
     committed STEP files (round2 R2-D17). Re-export the STEP on your machine
     (`kicad-cli pcb export step --subst-models`) before using it for fit checks. J2 is the tallest part, at 5.5 mm.
5. **1:1 paper print** of both boards (File → Print, 100 %, check with a ruler). Sit real parts on it if they have
   arrived: tact switch, USB-C, PH header, 2835 LED. Check the LED board against the printed moon-base cup pocket
   (Ø18.4) or the `jig_led_board` print.

## 2. Gerber check
1. Open `fab/main-board/v0.1/main-board-v0.1-gerbers.zip` and `fab/led-board/v0.2/led-board-v0.2-gerbers.zip` in
   KiCad's Gerber viewer: one layer at a time. On the LED board, check the bottom paste layer has the LP5012's
   exposed pad split into windows (not one full opening) and that the 0.15 mm tracks between its pins are intact.
2. Upload the same zip to the fab's online viewer and compare.

## 3. Order (Matt)
Board specs (also in each `FAB_NOTES.md`):

| | Main board | LED board |
|---|---|---|
| Size | 35 × 62 mm | **Ø 18 mm** round (no breakaway-tab nubs: it sits in an 18.4 mm pocket) |
| Layers / thickness | 2 / 1.6 mm FR4 | 2 / **1.0 mm** FR4 |
| Copper | 1 oz | 1 oz |
| Finish | HASL lead-free (ENIG optional) | **ENIG** (flat pads for the LEDs and the 0.4 mm-pitch WQFN) |
| Mask / silk | green / white | **white / black** (white mask reflects light into the moon) |
| Min track/space, via | 0.2/0.2 mm, 0.6/0.3 mm | **0.15/0.15 mm**, 0.6/0.3 mm, tented |
| Qty | 5 | 5 |
| Stencil | yes (frameless, top only) | yes (frameless, **top 0.12 mm and bottom 0.10 mm**) |

* **Main board: bare boards + stencils, hand assembly with Farnell parts.** **LED board v0.2: decide** between hand
  assembly (stencil + hot plate; only if you already do QFNs) and JLCPCB Economic assembly of its bottom face (U1, U2,
  R1, C1–C4), then hand-fit the top (`bom/assembly_routes.md`, recommended).
* For any fab assembly: upload that board's `bom_pcbway.csv` + `cpl_pcbway.csv` (PCBWay) or `bom_jlcpcb.csv` +
  `cpl_jlcpcb.csv` (JLCPCB; fill the LCSC column from their search), limit it to the side you want assembled, and
  check every part's rotation in the fab's placement preview (KiCad zero-orientation ≠ reel orientation). Small boards may need
  panelising for assembly at PCBWay (main 35 × 62 mm, LED Ø18 mm).
* After ordering: commit with the order reference in the message, tag `main-board-v0.1` / `led-board-v0.2`.

## Done when
Both boards ordered (or a decision recorded not to), order references committed, tags pushed.
