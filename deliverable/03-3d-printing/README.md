# 03: 3D printing (Bambu Lab X2D, 0.4 mm nozzle)

Every part is already in print orientation, so **do not auto-orient**. Each part has an `.stl` and a
`.3mf` (same geometry; use whichever your slicer prefers) and a preview image. The settings are in
`print-settings.pdf`; the step-by-step is in `handoff-03-printing.pdf`. Only Matt starts prints.

## `1-coupons-print-first/`: Coupons: print and check these first (fits, bayonet, lithophane contrast)

| Part | Qty | Material | Process | Size (mm) | Checks |
|---|---|---|---|---|---|
| `coupon_fit` | 1 | petg-basic | 0.20-standard | 70.0 x 36.0 x 8.5 | PASS |
| `coupon_bayonet_cup` | 1 | petg-basic | 0.16-fine | 20.8 x 21.6 x 4.9 | PASS |
| `coupon_bayonet_skirt` | 1 | pla-basic-white | 0.12-fine | 31.7 x 31.7 x 7.0 | PASS |
| `coupon_litho_wedge` | 1 | pla-basic-white | 0.12-fine | 86.0 x 14.0 x 3.2 | PASS |

## `2-moon-head/`: Moon head: lithophane moon, LED base cup, PETG clamp ring

| Part | Qty | Material | Process | Size (mm) | Checks |
|---|---|---|---|---|---|
| `moon_shell` | 1 | pla-basic-white | 0.12-fine | 50.0 x 50.0 x 51.5 | PASS |
| `moon_base` | 1 | petg-basic | 0.16-fine | 20.8 x 21.6 x 10.2 | PASS |
| `moon_ring` | 1 | petg-basic | 0.12-fine | 19.8 x 19.8 x 0.8 | PASS |

## `3-pack/`: Pack: front shell, back plate, book clip, button caps

| Part | Qty | Material | Process | Size (mm) | Checks |
|---|---|---|---|---|---|
| `pack_front` | 1 | petg-basic | 0.20-standard | 39.3 x 76.9 x 18.6 | PASS |
| `pack_back` | 1 | petg-basic | 0.20-standard | 35.3 x 73.8 x 3.8 | PASS |
| `pack_clip` | 1 | petg-basic | 0.20-standard | 34.0 x 61.3 x 3.7 | PASS |
| `button_caps` | 1 plate (3 caps) | petg-basic | 0.12-fine | 33.0 x 9.0 x 4.3 | PASS |

## `4-assembly-jig/`: Assembly aid: LED-board jig for the second-side stencil and reflow

| Part | Qty | Material | Process | Size (mm) | Checks |
|---|---|---|---|---|---|
| `jig_led_board` | 1 | petg-basic | 0.20-standard | 32.0 x 32.0 x 4.0 | PASS |

Materials: white PLA for the moon and the step wedge, and PETG for everything else, because it sits next
to warm electronics. `moon_ring` must be PETG: it keeps the PLA moon off the warm LED board.
Slicer overrides (walls, infill, brim) for the moon are in `print-settings.pdf`.
