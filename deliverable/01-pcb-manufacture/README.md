# 01: PCB manufacture

Two boards, rev 0.1. For each board, upload **`<board>-v0.1-gerbers.zip`** to the fab and copy the specs from
**`FAB_NOTES.pdf`** (or `.md`) into the order form. Instructions: `handoff-01-pcb-order.pdf`.

| Board | Size | Stack | Finish / mask | Stencil | Qty |
|---|---|---|---|---|---|
| `main-board/` (in the pack) | 35 × 62 mm | 2 layers, 1.6 mm FR4, 1 oz | HASL lead-free, green / white silk | top, 0.12 mm | 5 |
| `led-board/` (in the moon base) | Ø 26 mm round | 2 layers, **1.0 mm** FR4, 1 oz | **ENIG, white mask / black silk** | top **and** bottom, 0.12 mm | 5 |

Files per board:
- `*-gerbers.zip`: Gerber X2 for every layer, plus PTH and NPTH Excellon drill files. **This is the upload.**
- `FAB_NOTES.*`: board spec, special requests, what the remaining DRC warnings mean.
- `*-schematic.pdf`, `*.step`: some fabs ask for these. The STEP lacks 3D models for J1, J2, F1 and the 2835 LEDs;
  re-export it locally before using it for fit checks.
- `optional-assembly-service/`: BOM and placement files for PCBWay or JLCPCB, **only if you choose fab assembly**.
  The recommended route is bare boards plus hand assembly (`02-parts-order/assembly-routes-cost-comparison.pdf`).
- `images/`: top and bottom renders for a visual check against the fab's online viewer.

`kicad-source/`: the generated KiCad 9 projects with their project symbol and footprint library, so the
`../lib` paths resolve. PCBWay can take a `.kicad_pcb` directly. These are generated from `hardware/<board>/design.py`;
edit the Python, not these files.

Check results: main-board ERC 0, DRC errors 0,
unconnected 0; led-board ERC 0, DRC errors
0, unconnected 0.
