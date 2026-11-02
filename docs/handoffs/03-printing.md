# Handoff 03: 3D printing (Bambu X2D)

**For:** Claude Code in VS Code, in the `14MM47/3dprint` workflow, with Matt at the printer.
**Only Matt starts prints.** He types CONFIRM or presses print; Claude never runs `x2d print`.

The print-ready files are `print/<part>.stl` and `print/<part>.3mf`. The geometry is already in print orientation,
so don't let the slicer re-orient it. Settings, sizes and check results: [`print/README.md`](../../print/README.md)
(generated). Every part builds PASS through the 3dprint-contract checks.

| Order | Part | Material | Process | Notes |
|---|---|---|---|---|
| 1 | `coupon_fit` | PETG | 0.20 mm | Bores for the gooseneck self-tap socket, the button caps, the skirt in the base bore, and the LED board pocket |
| 2 | `coupon_bayonet` | PETG | 0.16 mm | Lugs enter, turn 30° and pull down onto a 1.0 mm disc, without forcing (VERIFY M4) |
| 3 | `coupon_litho_wedge` | **white PLA** (the moon's spool) | 0.12 mm | 0.6–3.0 mm steps. Backlight it with the LED board for VERIFY O1 |
| 4 | `moon_base` | PETG | 0.16 mm | Upright, no supports |
| 5 | `moon_ring` | PETG | 0.20 mm | 0.6 mm clamp ring (3 layers). Keeps the PLA moon off the warm LED board (round1 F5). **Do not print it in PLA** |
| 6 | `pack_front` | PETG | 0.20 mm | Face down |
| 7 | `pack_back` | PETG | 0.20 mm | Outer face down |
| 8 | `pack_clip` | PETG | 0.20 mm | Flat, layers along the arm |
| 9 | `button_caps` | PETG | 0.12 mm | One plate of 3 caps, flange down. Use a brim |
| 10 | `moon_shell` | **white PLA** | 0.12 mm, 6 walls, 100 % infill | 3 mm outer brim (only the skirt ring touches the bed). The inner dome closes as a short bridge at the top, which is expected |
| — | `jig_led_board` | PETG | 0.20 mm | Assembly aid for the LED board's second side (handoff 05 §2). Print it before the boards arrive |

## Steps
1. Print the coupons first (rows 1–3). Record which fits work in `docs/verification/VERIFY.md` (M2–M4, O1). If they
   differ from the defaults in `cad/parts/_lib/moonlib.py` / `packlib.py`, change those constants and rebuild:
   ```bash
   python cad/tools/pipeline.py cad/parts/<part>.py --out out/<part>
   ```
   The build must PASS. Never relax a check. Then run `python cad/tools/export_print.py` to refresh `print/`.
2. Measure the delivered gooseneck thread and nut (VERIFY M1) and the battery (M7) **before** printing `moon_base`
   and `pack_back`.
3. Slicing: once the 3dprint pipeline's A-tasks exist, use `/slice` / `/make` on these modules. Until then, open
   the 3MF in the Bambu Studio GUI. Select the X2D with a 0.4 mm nozzle, pick the material and process above, apply
   the per-part overrides from `print/README.md`, slice, and check the preview. Treat slicer warnings like check
   failures: fix the part, never suppress the warning.
4. Print the moon last, after the step wedge has confirmed that the 0.9–2.6 mm range gives good contrast (VERIFY M11).

## Done when
All parts are printed, the coupon results are recorded, and any constant changes are committed with PASS builds.
