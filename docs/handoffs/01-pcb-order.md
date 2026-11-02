# Handoff 01 — PCB final review and order

**For:** Claude Code in VS Code + KiCad 9 GUI, with Matt. ~45 min. **Matt places the order.**

The boards were generated, routed and checked in the cloud (KiCad 9.0.9, kicad-cli): ERC 0, DRC 0 errors,
0 unconnected, schematic parity clean. That run was after verification round 1; see `docs/verification/round1.md`
for what changed (Q4 LED-board switch, F1 PTC, R3 3.9 k, R5 10 k, R11 VREF, J2 moved with a lead slot, LM75B
thermostat wiring). The fab packages are ready in `fab/main-board/v0.1/` and `fab/led-board/v0.1/`. The DRC
warnings that remain are silk-only, and the reports list them: the main board's SW1 outline is clipped at the board
edge, because the knob overhangs the edge by design.
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
   * LED board: 1.0 mm thick, with the LEDs on top and the TLC59116, LM75B and G/V/D/C pads underneath.
5. **1:1 paper print** of both boards (File → Print, 100 %, check with a ruler). Sit real parts on it if they have
   arrived: tact switch, USB-C, PH header, 2835 LED. Check the LED board against the printed moon-base cup pocket.

## 2. Gerber check
1. Open `fab/<board>/v0.1/<board>-v0.1-gerbers.zip` in KiCad's Gerber viewer: one layer at a time.
2. Upload the same zip to the fab's online viewer and compare.

## 3. Order (Matt)
Board specs (also in each `FAB_NOTES.md`):

| | Main board | LED board |
|---|---|---|
| Size | 35 × 62 mm | Ø 26 mm round |
| Layers / thickness | 2 / 1.6 mm FR4 | 2 / **1.0 mm** FR4 |
| Copper | 1 oz | 1 oz |
| Finish | HASL lead-free (ENIG optional) | **ENIG** (flat pads for LEDs/TSSOP) |
| Mask / silk | green / white | **white / black** (white mask reflects light into the moon) |
| Min track/space, via | 0.2/0.2 mm, 0.6/0.3 mm | 0.2/0.15 mm, 0.5/0.25 mm |
| Qty | 5 | 5 |
| Stencil | yes (frameless, top only) | yes (frameless, **top and bottom**) |

* **Route chosen: bare boards + stencils, hand assembly with Farnell parts** (see `bom/assembly_routes.md` for the
  price comparison of all three routes). If Matt prefers assembly instead: upload `bom_pcbway.csv` + `cpl_pcbway.csv`
  (PCBWay) or `bom_jlcpcb.csv` + `cpl_jlcpcb.csv` (JLCPCB; fill the LCSC column from their search), and check every
  part's rotation in the fab's placement preview (KiCad zero-orientation ≠ reel orientation). Small boards may need
  panelising for assembly at PCBWay (both are < 50 × 50 mm).
* After ordering: commit with the order reference in the message, tag `main-board-v0.1` / `led-board-v0.1`.

## Done when
Both boards ordered (or a decision recorded not to), order references committed, tags pushed.
