# sim/: SPICE simulations of the moon reading light

`python3 sim/run_sims.py` runs every case, checks the results against their limits and writes
`docs/verification/spice-report_main-v<rev>_led-v<rev>_rev<N>.md` and `.pdf` (report revision `REPORT_REV` in
`sim/report.py`; earlier revisions are kept; board revisions read from
`hardware/*/design.py`; PDF via WeasyPrint) with its figures in `docs/verification/spice/`. It takes about 30 s.

Needs ngspice (42 tested; XSPICE not required), numpy, matplotlib, schemdraw, markdown, weasyprint (PDF; skipped if missing). kicad-cli and pdftoppm
are optional (they add the board schematics to the report's appendix).

| File | What it is |
|---|---|
| `models.inc` | device models (DMG2305UX, bias-dependent MLCCs, LiPo cell, S1J, SMF5.0A, LEDs, LP5012 sink), each fitted to datasheet points; PROVISIONAL values are marked |
| `boards.inc` | the main-board power path and the LED board as subcircuits (reference designators kept), plus the neck cable |
| `cases/*.cir` | one netlist per scenario, with `.param` defaults that `run_sims.py` overrides per variant |
| `run_sims.py` | the variant matrix, the checks (limit and source for each) and the entry point |
| `spice.py` | runs one variant: templating, ngspice in batch mode, `.meas` parsing, `wrdata` loading |
| `plots.py`, `schematics.py`, `report.py` | figures, schematic drawings, Markdown + self-contained HTML report |
| `out/` | netlists as run, ngspice logs, raw data, `results.json`, `report.html` (not committed) |

These are predictions, not evidence. When a bench measurement (docs/verification/VERIFY.md) replaces a
PROVISIONAL value, change it in `models.inc` or `boards.inc` and re-run.
