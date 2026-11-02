# Moon reading light v0.1: deliverable pack

This folder holds everything needed to manufacture, print, flash, assemble and test the lamp, in build order. It is
**generated** by `python3 tools/build_deliverable.py` from commit `67f9752`.
Don't edit it by hand: change the design, then re-run the generator. `MANIFEST.txt` lists every file with its
SHA-256 and its source in the repo.

**Nothing has been ordered.** Matt places every order and starts every print. The design has been through two
verification rounds; it has not been built or tested on hardware yet.

## Build order

| Step | Folder | What you do | Instructions |
|---|---|---|---|
| 0 | `00-overview/` | Read the plan, look at the renders, check the open decisions | `00-START-HERE.pdf`, `PLAN-…pdf` |
| 1 | `01-pcb-manufacture/` | Upload each board's Gerber zip to PCBWay (or JLCPCB) with the specs in its `FAB_NOTES` | `handoff-01-pcb-order.pdf` |
| 2 | `02-parts-order/` | Paste `farnell_quickpaste.txt` into Farnell's Quick Paste; buy the off-board items | `handoff-02-parts-order.pdf` |
| 3 | `03-3d-printing/` | Print the coupons first, then the moon head, the pack and the jig | `handoff-03-printing.pdf` |
| 4 | `04-firmware/` | Set the fuses once, then flash `release/` (or `debug/` for bring-up) | `handoff-04-firmware.pdf` |
| 5 | `05-assembly-and-bring-up/` | Assemble the boards, cable, moon and pack; first light | `handoff-05-assembly-bringup.pdf` |
| 6 | `06-test-and-verification/` | Bench checklist: electrical, firmware, thermal, optical, fit | `VERIFY-bench-checklist.pdf` |
| 7 | `07-design-reference/` | Background: electronics notes, datasheet specs, research | — |

## Status of the files in this pack

| Board | ERC | DRC errors | DRC warnings | Unconnected | Schematic parity |
|---|---|---|---|---|---|
| main-board | 0 | 0 | 2 | 0 | 0 |
| led-board | 0 | 0 | 0 | 0 | 0 |

The main board's 2 DRC warnings are intended: the slide-switch outline crosses the board edge where its knob
overhangs. Every printed part passes the 3dprint-contract checks (11 parts). The firmware's 29 host tests
pass, and all four builds compile without warnings.

## Decisions still open for Matt
See `00-overview/open-decisions-and-round1-summary.pdf` §5. In short:
1. Reading brightness is 20–30 lux on the page, which suits a moon lamp, not a full reading light. v0.2 option: a
   downward reading LED.
2. No cell-temperature sensing on the charger, so charge at room temperature. v0.2 option: an NTC charger.
3. Soft-orange night mode includes some warm white (recommended: keep it).
4. Green/blue drift at low battery (accepted for v0.1).

## Safety rules that apply to every step
- Meter the battery lead before plugging it in: + goes to J2 pin 1 (silk "+").
- Never power the board from a programmer or USB-UART: J4 pin 1 is a sense line only.
- Charge at room temperature, and stop using a pouch that swells.
- Do not use anaerobic thread-locker on the printed parts (it crazes PETG).
