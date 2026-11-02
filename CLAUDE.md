# CLAUDE.md: reading_light

Moon reading light: a clip-on book light. A pack clips to the back cover; a ~12 cm gooseneck rises from it; a 50 mm
lithophane moon at the end glows from LEDs in its base. Matt's personal project (keep it consumer/hobby; no
industrial-control subject matter).

Read [`PLAN.md`](PLAN.md) first: requirements (R-numbers), architecture, decisions, status. Then the area you touch.

## Where things are
| Area | Path | Process it follows |
|---|---|---|
| Electronics (2 boards) | `hardware/` (`main-board/`, `led-board/`, `lib/`, `tools/kigen/`) | `14MM47/pcb` CLAUDE.md conventions (KiCad 9, kicad-cli, ERC/DRC clean, fab per revision) |
| Fabrication outputs | `fab/<board>/v<rev>/` | committed per ordered revision |
| Firmware | `firmware/` (PlatformIO, megaTinyCore) | pcb repo firmware conventions |
| Printed parts | `cad/parts/*.py`, `cad/tools/pipeline.py` | `14MM47/3dprint` part contract (B-requirements, PRINT, VERIFY, claims, checks) |
| Print-ready files | `print/` | STL + 3MF per part, settings in `print/README.md` |
| BOM / order | `bom/` | Farnell UK order list + off-board items |
| Design notes, reviews | `docs/design/`, `docs/verification/` | |
| Laptop handoffs | `docs/handoffs/` | for Claude Code in VS Code |

## Rules
- The Python design files are the source of truth. `hardware/<board>/design.py` generates the schematic **and** the
  board; never hand-edit the generated `.kicad_sch`/`.kicad_pcb` and then regenerate (edits would be lost). If you
  finish a board by hand in KiCad, say so in PLAN.md and stop regenerating that board.
- Build: `python3 hardware/build.py <board>` (needs KiCad 9's Python `pcbnew`); it must end with ERC 0, DRC 0 errors,
  0 unconnected, 0 parity. `python3 hardware/build.py <board> --fab` writes `fab/<board>/v<rev>/`.
- Firmware: `cd firmware && pio test -e native && pio run`. Mode recipes come from `tools/gen_modes.py`;
  `include/board_map.h` is generated from the LED board design - never edit either by hand.
- CAD: `python -m cad.tools.pipeline cad/parts/<part>.py --out out/<part>` (or `python cad/tools/pipeline.py ...`).
  Never relax a check to get a PASS; per-part overrides need a `why` (3dprint rule).
- Never order, pay, or upload to a fab or distributor. Produce files; Matt orders.
- Any value nobody has measured is a VERIFY item (gooseneck thread, nut size, LED bins, PLA transmission...).
