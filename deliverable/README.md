# Moon reading light v0.2 (main board v0.1, LED board v0.2): deliverable pack

This folder holds everything needed to manufacture, print, flash, assemble and test the lamp, in build order. It is
**generated** by `python3 tools/build_deliverable.py` from commit `910de4c`.
Don't edit it by hand: change the design, then re-run the generator. `MANIFEST.txt` lists every file with its
SHA-256 and its source in the repo.

**Nothing has been ordered.** Matt places every order and starts every print. The design has been through three
verification rounds; it has not been built or tested on hardware yet. **What changed in v0.2** (the 18 mm LED board
with the TI LP5012 driver, one RGB LED, the slim moon head, and a corrected optics model):
`00-overview/what-changed-in-v0.2.pdf`.

## Build order

| Step | Folder | What you do | Instructions |
|---|---|---|---|
| 0 | `00-overview/` | Read the plan and what changed in v0.2, look at the renders and `fitment/` views, check the open decisions | `00-START-HERE.pdf`, `PLAN-…pdf` |
| 1 | `01-pcb-manufacture/` | Upload each board's Gerber zip to PCBWay (or JLCPCB) with the specs in its `FAB_NOTES`; decide how the LED board's WQFN side is assembled | `handoff-01-pcb-order.pdf` |
| 2 | `02-parts-order/` | Paste `farnell_quickpaste.txt` into Farnell's Quick Paste; the LP5012 from DigiKey UK (`digikey_order.csv`); buy the off-board items | `handoff-02-parts-order.pdf` |
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
overhangs. Every printed part passes the 3dprint-contract checks (12 parts). The firmware's host tests
pass, and all five builds compile.

## Decisions still open for Matt
See `00-overview/verification-round3-and-open-decisions.pdf`, last section. In short:
1. LED board assembly: the LP5012 is a 0.4 mm-pitch WQFN. Hand assembly needs a stencil and a hot plate; the
   recommendation is fab assembly of that board's bottom face (`02-parts-order/assembly-routes-cost-comparison.pdf`).
2. Green/blue headroom: keep R1 2.94 kΩ (recommended; decide after VERIFY E9 measures the received dies) or 3.65 kΩ
   (20 mA on every channel, −20 % white).
3. LP5012 VCAP/RIREF ground returns run ~22–26 mm: order as is and scope it (VERIFY E18, recommended) or re-lay the
   board centre first.
4. The LED board is not keyed and may turn ±30° with the moon (recommended: accept).
5. Carried over: reading brightness 20–30 lux (a downward reading LED in the next revision); no cell-temperature
   sensing on the charger, so charge at room temperature (an NTC charger in the next revision); soft-orange night
   mode includes some warm white (recommended: keep it).

## Safety rules that apply to every step
- Meter the battery lead before plugging it in: + goes to J2 pin 1 (silk "+").
- Never power the board from a programmer or USB-UART: J4 pin 1 is a sense line only.
- Charge at room temperature, and stop using a pouch that swells.
- Do not use anaerobic thread-locker on the printed parts (it crazes PETG).
