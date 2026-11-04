# Handoff 03: 3D printing (Bambu X2D)

**For:** Claude Code in VS Code, in the `14MM47/3dprint` workflow, with Matt at the printer.
**Only Matt starts prints.** He types CONFIRM or presses print; Claude never runs `x2d print`.

The print-ready files are `print/<part>.stl` and `print/<part>.3mf`. The geometry is already in print orientation,
so don't let the slicer re-orient it. Settings, sizes and check results: [`print/README.md`](../../print/README.md)
(generated). Every part builds PASS through the 3dprint-contract checks. The moon head is the v0.2 design
(2026-11-03, `docs/design/led-board-v0.2.md` §6; round 3: clamp spring, clockwise lock, jam nut): the moon's Ø25.3 mm
skirt slides over a slim Ø20.8 mm cup and locks with an inside-out bayonet (lugs on the cup, grooves in the skirt).

| Order | Part | Material | Process | Notes |
|---|---|---|---|---|
| 1 | `coupon_fit` | PETG | 0.20 mm | Gooseneck self-tap socket trials (9.1–9.5 mm) and button-cap holes (7.2–7.6 mm); dots index the sizes |
| 2a | `coupon_bayonet_cup` | PETG | 0.16 mm | The cup's top (pocket, land, lugs), cut on one of the real cup's layer boundaries |
| 2b | `coupon_bayonet_skirt` | **white PLA** (the moon's spool) | 0.12 mm, 6 walls, 100 % infill, 3 mm brim | The moon's real skirt, grooves, clamp cone and bore, in the moon's own material so the fit is the real one. Test: an 18 mm disc (or a bare LED board) and a `moon_ring` in the cup, slide the skirt over, lugs into the slots, turn **clockwise** (seen from the top) 30° until it stops. It must lock by hand without forcing, show no whitening at the groove ends, and hold the disc without rattle. Repeat with 0.9, 1.0 and 1.1 mm discs (the board's ±10 %). Tune `LOCK_OFFSET` (VERIFY M4, M5) |
| 3 | `coupon_litho_wedge` | **white PLA** (the moon's spool) | 0.12 mm | 0.6–3.0 mm steps. Backlight it with the LED board for VERIFY O1 |
| 4 | `moon_base` | PETG | 0.16 mm | Upright, no supports. The lugs' 45° faces print without support |
| 5 | `moon_ring` | PETG | **0.12 mm** | 0.8 mm clamp ring (0.2 + 5 × 0.12 mm layers), ID 16.4, 45° chamfer on the top outer edge (chamfer up). It is the clamp's spring: it rolls over the board edge into the 0.4 mm gap above the cup's land. Keeps the PLA moon off the warm LED board (round1 F5). **Do not print it in PLA**. Print three: one for the coupon, one spare |
| 6 | `pack_front` | PETG | 0.20 mm | Face down |
| 7 | `pack_back` | PETG | 0.20 mm | Outer face down |
| 8 | `pack_clip` | PETG | 0.20 mm | Flat, layers along the arm |
| 9 | `button_caps` | PETG | 0.12 mm | One plate of 3 caps, flange down. Use a brim |
| 10 | `moon_shell` | **white PLA** | 0.12 mm, 6 walls, 100 % infill | 3 mm outer brim (only the skirt ring touches the bed). The bayonet grooves inside the skirt have 45° roofs and floors, no supports. The inner dome closes as a short bridge at the top, which is expected |
| — | `jig_led_board` | PETG | 0.20 mm | Assembly aid for the 18 mm LED board's second side (handoff 05 §2). Print it before the boards arrive |

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
