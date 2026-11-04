# Round 3: mechanical / printing / optics review of the v0.2 moon head

Reviewer: independent (mechanical, 3D printing, optics). Date 2026-11-04. Scope: `cad/parts/_lib/moonlib.py`,
`moon_shell`, `moon_base`, `moon_ring`, `coupon_bayonet`, `jig_led_board`, `print/`, `docs/design/fitment/`,
`docs/design/optics/head_v02.py`, `docs/design/led-board-v0.2.md` §5–6, handoffs 03/05, VERIFY M/O items.
I changed no repo files. All five head parts were rebuilt in scratch with the CAD env and still PASS. Scratch
scripts (layer-staircase estimate, groove probe, optics variants) are in
`/tmp/claude-0/-home-user/7ba8e87c-d4ee-5a66-9891-51bde4e0a9a7/scratchpad/rv3/`.

## Summary

The optics are right, and so are most of the head's clearances. The aperture model is now correct: a ray is blocked
only if it crosses the opening plane outside r 9.0. Nothing solid enters the emitter-to-opening cone. The PLA
never touches the board.

The weak point is the clamp. In the CAD the locked bayonet is **line-to-line**: the groove floor at the lock end
equals the lug underside, and the cone sits exactly on the ring chamfer. So the cam does **not** preload anything,
whatever the docs say, and the knob VERIFY M4 names (`CAM_DROP`) does not change the locked fit.

The real fit is therefore set by things nobody controls:
- board thickness ±0.1;
- the layer staircases on the four mating 45° faces, which I estimate add 0.15–0.25 mm of interference.

The only compliance in the stack is the ring rolling over a 0.1 mm gap. The coupon meant to catch this is printed
in PETG, not the moon's PLA.

There is also a second problem. Nothing reacts the captive nut. Locking the moon (CCW seen from the top, checked
on the STL) is the unscrewing direction of the M10×1 thread, so the moon twist can back the cup off the neck and
twist the soldered cable.

Count: 4 MAJOR, 4 MINOR, 4 NOTE.

## Findings

| ID | Sev | Finding and evidence | Fix |
|---|---|---|---|
| R3-M1 | **MAJOR** | **The cam gives no designed preload. The stack's only compliance is a 0.08 mm ring roll, so the fit ends up binding (and may crack the PLA skirt) or rattling, depending on print effects.** (1) CAD: `FLOOR_K_LOCK = LUG_BOT_K` (moonlib.py:94) and `CONE_C` lies on the chamfer line (moonlib.py:47). The locked interference is therefore exactly 0. The 0.35 mm lead-in (`FLOOR_K_OPEN`) only lets the lug enter, and the moon already sits on the ring by gravity. CAD closure vs board thickness: 0.9 mm gives 0.10 mm play, 1.0 gives 0, 1.1 gives 0.10 interference. (2) As printed, sliced at layer mid-height (Bambu: first layer 0.2; moon 0.12, cup 0.16, ring 0.20), the ring's 2-step chamfer puts its step corners 0.10 above the 45° line. Results: cone/ring −0.154 mm (the moon's cone steps add 0.06); lug/floor −0.106 (0.08 + 0.06); ledge prints 0.02 low. Net **≈ −0.24 mm interference** for a 1.0 board, perhaps −0.15 once bead rounding is allowed for. With the board tolerance: 0.9 gives −0.14, 1.1 gives −0.34 (`rv3/stairs.py`). (3) Compliance: the cone bears at r 9.5–9.9, outboard of the board (r ≤ 9.0). The ring therefore pivots on the board edge and rolls until its OD meets the land, 0.1 below. Estimate: ≈250 N/mm at the cone, travel 0.08 mm (≈20 N). With a 0.9 board the ring already rests on the land, so it has **no** travel. Everything beyond that goes into the 45° lug/floor wedge, i.e. PLA skirt hoop + PETG cup. Free-ring estimate for the skirt band below the floor (2.1 × 2 mm, 3 loads, E 3.5 GPa): **≈22 N per lug and ≈30 MPa per 0.1 mm of radial wedge**, which is close to Bambu PLA's ~35 MPa. Turning torque at ~100 N clamp is ≈1 N·m. If the step corners crush instead, a 0.9 board leaves the moon with ~0.1 mm play, and nothing then stops it rotating back toward the slots. (4) The PLA skirt carries the preload as sustained hoop tension at the hottest PLA point (TC3 pass limit 47 °C), so creep relaxes it (T7). B11 (moon_base.py:21–22), led-board-v0.2.md:116–117, PLAN §2 Mechanics, handoff 05 §3.5 and VERIFY M4 all say "the cam pulls/preloads". The CAD does not | Make the preload a designed spring, not a stack accident. (a) Lower the land: `Z_LAND = Z_BOARD_TOP - 0.3` (was −0.1). The ring then gets ~0.23 mm of roll travel at the cone (~60 N at full travel, PETG strain ~1.5 %), which covers board ±0.1 plus the staircase. The pocket wall stays 0.7 mm (B11 claim > 0.5 still holds), and the land becomes 1.05 mm wide. (b) Add `LOCK_OFFSET`, with `FLOOR_K_LOCK = LUG_BOT_K + LOCK_OFFSET`, starting at 0.0 after (a). (c) Print the ring at 0.12-fine: 0.2 + 5 × 0.12 = 0.8, a 3-step chamfer, so corners protrude 0.06 instead of 0.10. (d) Add a claim: lock closure for `BOARD_T ± 0.1` lies inside the ring's roll travel (≥ 0.03 preload, ≤ travel). (e) Reword B11/§6/handoff/M4 to "the ring's roll over the lowered land is the spring" |
| R3-M2 | **MAJOR** | **VERIFY M4 names the wrong tuning knob.** M4 (VERIFY.md:80) says "tune `CAM_DROP` if it is loose or binds". `CAM_DROP` only enters `FLOOR_K_OPEN` and `Z_SKIRT_BOT` (moonlib.py:95–96), i.e. the lead-in at the slot and the skirt length. The locked position is untouched. The M5 remedy "add a 0.2 mm shim ring" adds 0.2 mm of rigid interference on top of the −0.15…−0.34 above | M4: tune `LOCK_OFFSET` (R3-M1b), lower = looser, in 0.05 mm steps. M5: shims only after (a); prefer ring variants at 0.12-mm layers (0.68 / 0.80 / 0.92) chosen after measuring the board (M6) |
| R3-M3 | **MAJOR** | **The bayonet coupon does not test the moon's fit.** The geometry is cut from the real parts (B1 holds). But the whole coupon is PETG at 0.16 mm (coupon_bayonet.py:19; handoff 03 row 2), while the moon is white PLA at 0.12 mm with 6 walls and 100 % infill. That changes (1) stiffness (PETG ~2.0 vs PLA ~3.5 GPa, and PETG is ductile: a fit that cracks a PLA skirt passes in PETG); (2) the staircase (0.08 vs 0.06 mm corners); (3) friction (PETG on PETG is grabby; the real pair is PLA on PETG); (4) shrinkage and hole sizing for the 0.15 mm slip. Also the cup half is cut at cup z 5.546, 0.106 mm out of layer phase with the real cup (5.546 mod 0.16), so its lug steps differ from the real ones. The test uses only a 1.0 mm disc | Split it into `coupon_bayonet_skirt` (moon's PLA spool, 0.12-fine, the moon's slicer overrides) and `coupon_bayonet_cup` (PETG 0.16). Cut the cup half at `z0 = 0.16 * floor((moon_z0 - 1.0)/0.16)` (= 5.44) so its layers coincide with the real cup's. Test with 0.9, 1.0 and 1.1 mm discs (board ±10 %). Record the torque feel and any whitening at the groove ends |
| R3-M4 | **MAJOR** | **Nothing reacts the captive nut, and locking the moon is the unscrewing direction.** (1) The single M10×1 nut sits in the socket above the floor (moon_base B6). Nothing under the floor carries the clamp: the BOM has "M10x1 male ends" on a Ø10 tube (thread OD = tube OD, no shoulder), and head_section.png shows a plain tube under the floor. So the cup is held only by friction on an unloaded thread. Handoff 05 §3.3 does not even put CA gel on this thread (B6 asks for it). (2) The STL probe (`rv3/groove_probe.py` on print/moon_shell.stl) shows the lock floor at 82.5–97.5°, the ramp to 110° and the slot at 110–131° at r 11. The moon therefore turns **+30° about +z (CCW seen from the moon's top) to lock**, which is the loosening direction of a right-hand thread on the cup. Every lock, under the cam friction of R3-M1, can back the cup off. The board sits in the cup on its cable, so the cable twists without limit. (3) Handoff 05 §3.5 says to hold the cup when *removing*. Removal is CW, the tightening direction; the risky step is *locking*. (4) The lock direction is also the opposite of the jar-lid habit | (a) Add a second M10×1 nut + washer under the floor and jam the floor between the two nuts before the board is soldered: BOM 2 nuts per lamp, rule in B6. Or confirm a ≥ Ø12 shoulder on the delivered gooseneck (add it to VERIFY M1). The protrusion rule then covers 3 + 2 + 3 = 8 mm of thread. (b) CA gel on the moon-end thread in §3.3. (c) Optional: mirror the bayonet so locking is CW from the top. In `moon_shell.part()` put the slot at `a - BAYONET_TURN_DEG` and mirror `a0/a1/ramp0/ramp1`. Then the high-torque lock tightens the thread. (d) §3.5: "hold the cup band below the skirt whenever you turn the moon". (e) The two-nut joint also lets the cup be clocked so the near side (B10) faces the reader at one of the 3 lock positions; add a dot on the cup at −Y |
| R3-M5 | MINOR | **Handoff 05 §3.3 nut step cannot be done as written.** "Spin the nut down into the hex socket": the socket stops the nut turning, and no 14 AF socket (~19–20 mm OD) fits the Ø16.7 cavity, so the last 3 turns must be the cup turning. Filing the thread "flush" after the cable is through the bore risks nicking the wires, and filings fall into the cup. The 15 mm of heat-shrink "where the wires leave each threaded end" cannot stand above the moon-end thread: only 4.0 mm is free (thread end ≤ nut top + 0.5 to the board underside at 9.5) | Rewrite: cut/file the thread to length (M12) **before** feeding the cable. Drop the nut in the socket, feed the wires through floor and nut, hold the gooseneck and turn the cup onto it (wires not attached yet, so no twist), jam it against the lower nut (R3-M4). At the moon end, keep the heat-shrink inside the bore, flush with the thread end |
| R3-M6 | MINOR | **The ring's ID edge can land on the white LEDs' anode solder.** The ring is centred by the cone, i.e. on the moon (±0.15 skirt slip). The board floats in the pocket: 0.2 radial, plus up to 0.1 for an undersize routed board. Worst offset ≈0.45 mm. Margins from the ring ID (r 8.0): 0.32 to the 2835 bodies (r 7.55 ends / 7.68 corners) and **0.12 to the anode-pad corners** (pad 2 to x +2.0, y ±1.1 at r 5.8, so r 7.88; design.py:38 says pads stay inside 7.8). So in a realistic 0.15–0.3 mm offset the ring sits on a solder fillet and tilts. At the extreme it bears on an LED end | `RING_R_IN = 8.2` (ID 16.4): margins 0.52 to the bodies, 0.32 to the pads, clamp overlap still 0.8 mm (the load sits at the board edge anyway, R3-M1). Make this a new moon_ring B-line and claim `RING_R_IN >= COMPONENT_R_MAX + 0.4`, and correct design.py's "pads inside 7.8" comment to 7.88 |
| R3-M7 | MINOR | **The moon's 82° overhang override covers more than its `why`.** The `why` (moon_shell.py:63–68) says it "only admits the interior". But the pipeline applies 82° to the whole part, and claim B8 checks only `rad > R_OUT-0.3 and z > Z_CUT+0.05` (moon_shell.py:304). So the cone, bore, groove roofs and slot ceilings (all below Z_CUT) are checked at 82° only. Today they are fine: 0 facets steeper than 45.5° below Z_CUT + 0.6 on print/moon_shell.stl (`rv3/overhang_low.py`). A later change to the bayonet would pass unnoticed (3dprint: overrides need a true `why`) | Add a claim to `moon_shell.spec`: overhang ≤ 45.5° for every facet with z < Z_CUT + 0.6 + SHIFT and z > 0.25 |
| R3-O1 | MINOR | **The optics model leaves out the RGB body as an occluder.** D9 is 2.8 × 3.5 mm and 2.05 mm tall in the KiCad STEP (RGB_TOP_H 1.9 in moonlib), i.e. 1.2–1.35 mm above the white emitter plane at the centre. White rays aimed across the centre below ~16–22° elevation hit it. Rerun with a box occluder (`rv3/opt/rgb_occl.py`, same physics, 160 × 120 grid): one white **1.011 → 1.028**, all whites **1.002 → 1.021** (H 1.9; 1.034 / 1.022 at H 2.05). Still invisible (< 3 %), but the 1.002 figure in PLAN §2, B13, design note §5 and VERIFY O4 is optimistic | Add the box occluder to `direct()` for the white sources in head_v02.py, regenerate head_v02.txt, and quote ~1.03 / 1.02 / 1.04 in B13, PLAN and O4 |
| R3-M8 | NOTE | **The board is not keyed, so it turns with the moon.** Cone friction torque ≈ √2·μF·9.7 > ring–board ≈ μF·9.0 ≈ board–ledge ≈ μF·8.7 (same PETG/mask pair). The ring always turns with the moon, and the board probably does too. The soldered cable sees ±30° per lock/unlock (reversible; the silicone strain relief takes it) | Accept, or (board not ordered yet) add a 1.0 × 0.5 mm notch in the copper-free band at r 8.5–9.0 and a matching key on the pocket wall |
| R3-M9 | NOTE | **Lead-in and direction cue.** The skirt's inner bottom edge is a sharp corner (`_skirt_profile`, (SKIRT_R_IN, Z_SKIRT_BOT)). First-layer squish on that inner perimeter eats into the 0.15 mm slip exactly where the user aligns the moon blind. Only feel shows the turn direction (the slot's far wall stops the wrong way: fine, but undiscoverable by eye) | 0.3 × 45° inner chamfer at the skirt bottom (a 45° overhang, printable; it leaves ≥ 0.9 mm under the open-end floor). Emboss a small lock arrow on the cup band below the skirt (cup z 1–6 is exposed) |
| R3-M10 | NOTE | **Docs vs CAD.** (1) moonlib.py:31 says LED_DEPTH "max/min ~1.05 (1.0 → 1.03, 2.0 → 1.12)"; head_v02.txt gives 1.011 / 1.012 / 1.055 (those comment numbers are the r 8.3 rows). moonlib.py:27 cites `docs/design/optics.md`, which does not exist. (2) moonlib.py:64: `R_RIDGE` "≈ (8.39, Z_CUT+0.03)" is really (8.564, Z_CUT−0.164) and is not in the geometry (the bore exists). coupon_bayonet.py:34 uses it (cap r_in 8.964 < bore 9.0), leaving a 0.036 mm downward sliver that the check reports as an "18 mm bridge". Use `BORE_R + 0.4`. (3) moonlib.py:24 "2835 body 0.8" vs Bridgelux DS312 0.7 (the value 0.7 is right). (4) moon_shell B12 and moon_base B9 still say a 0.6 mm ring (now 0.8). (5) head_exploded.png draws the nut **below** the cup floor; it lives in the socket above it. (6) print/README's "Check warnings" column lists thresholds, not values. The real minima, none structural: moon 0.997 (lithophane equator, by design ≥ 0.9), cup 1.145 (pocket lip at the bevel), ring 0.753 (chamfer diagonal of a 0.8 washer), coupon 0.999 (the cap sliver), jig 0.909 (relief-to-notch wall). (7) jig B2 uses 1.45 mm; the KiCad SOT-23-5 model is 1.55 from the board face (still < 2.0) | Correct the comments and requirement text (new B-lines, no renumbering). Fix the coupon cap radius. Put measured values in the README column. Re-render the exploded view with the nut above the floor |
| R3-O2 | NOTE | **The escape fraction is ~3 % high from discretisation.** Model eta (direct flux on the wall) is 0.979. The Monte-Carlo pass fraction of a Lambertian point 1.2 mm under an r 9.0 aperture is 0.970 / 0.952 / 0.902 at r 4.5 / 5.8 / 7.1 (mean ≈ 0.95). The grid's `R² sinθ` area element ignores the 22.4 → 23.25 radius change across the 40–50° band. So escape is ≈0.62, not 0.636, and O2 should expect ~38 lm (inside its ±20 %). Otherwise the series T·eta / (1 − ρ_eff) with T 0.20, ρ 0.70 is consistent (≈3.2 wall interactions, ~30 % absorbed) | Normalise eta by the analytic pass fraction, or use the slant-corrected area element |
| R3-O3 | NOTE | **"Visible wall" means θ > 50°, but a book light is seen from below.** The model gives whites ≥ 0.94 of the visible-wall mean down to θ 24° and the RGB 0.73–0.97 at 24–50° (`rv3/opt/lowband.py`), so the lighting is fine. With the slim stem, though, the 45° collar from θ ≈ 30° to 45° is now visible. It is a smooth cone 2.6–3.5 mm thick (`cone − R_IN`, vs the 0.9–2.6 relief), so it will read as a darker, featureless band | Say so in M11/O4 ("collar band darker by design, B8"). Optionally carry the relief down to 30° on the inside where the slope limiter allows |

## Checked and found correct

- **Aperture model** (head_v02.py:51–53). A ray is blocked iff its segment crosses z_cut at r > open_r. The model
  matches the CAD: z_cut −20.512, emitters at Z_EMIT −21.712 (board top + 0.7 = DS312 body height), ring r 5.8,
  ±1.3 spread, angles 22.5° + 45°·k as in design.py. The RGB sits +1.2 above the whites.
- **No solid in the emitter-to-opening cone:**
  - The bore r 9.0 equals the opening, so by convexity of the radial distance along a ray nothing passing the
    opening is clipped.
  - The cone is at r 9.6 at the emitter plane.
  - The ring top (−21.612) is 0.1 above the emitter plane; its ID 8.0 compares with a cone radius of 7.26 there
    (0.74 clear).
  - The cup land (r ≥ 9.2) sits below the emitter plane, and the lugs are far outside.
  - The 2835 tops are flush with the emitters, and R2 is 0.35 tall, so neither shades anything.
  - B14 probes: 0 hits.
- **LED depth is set by the ring and cone alone.** The moon references the board top through the ring, so board
  thickness does not move it. Ring ±0.05 gives depth 1.15–1.25 and max/min 1.011–1.012. The model table (1.0 / 1.2 /
  1.5 / 2.0 mm) matches the design note and PLAN. "≥ 2:1 above the opening" is backed by the round-1 table (2.0–2.05
  at +3 mm).
- **Thermal rule.** The PLA touches only the PETG ring's chamfer (r 9.5–9.9, outboard of the board) and the PETG
  cup/lugs. The nearest PLA–board distance is 0.92 mm (cone to the board's top edge). Without a ring the cone lands
  on the cup bevel, 0.67 mm from the board.
- **Under the board:**
  - Bottom parts: SOT-23-5 1.55 tall at r ≤ 7.25, C2 0.8, LP5012 0.8.
  - The ledge (r 8.35) clears the bottom parts even with a 0.3 mm board offset (8.1).
  - Free height: 4.5 mm (4.48 as sliced); 4.0 mm above a thread at nut top + 0.5.
  - Nut socket: corners at 8.31 inside the 8.35 cavity (no ceiling). The nut's corners (8.08) pass the cavity, and
    the wall to the OD at the socket corners is 2.09 mm.
  - The silicone blob limit of r ≈ 8 (J1 pad corner r 7.76) is consistent.
- **Bayonet geometry (from the STLs):**
  - The lug fits the slot with 0.5 mm each side at r 11.
  - Engagement 0.65 mm radial: lug OD 11.2 vs skirt ID 10.55. The groove back wall is 0.25 clear, more than the
    0.15 lateral float.
  - Lug top to roof: 0.27 perpendicular (≈0.24 vertical after layer steps).
  - Cone to cup bevel: 0.354 vertical nominal (≈0.23 after steps, ≈0.15 with full ring roll).
  - End stop 1° past lock. The cam rises 0.35 mm over 14.65° (7.1°); the last 15° is a flat dwell, so there is no
    back-drive.
  - Pull-off: the skirt cracks before 0.5 mm of wedge opening, far above the ~30 N per lug of bending the neck by
    the moon.
- **Lugs.** Root 2.1 × 2.8 mm. At 30 N per lug, ≈6 MPa bending, in the layer plane along the perimeter loop. Fine in
  PETG for repeated twisting.
- **Printability:**
  - No facet steeper than 45° in the moon's exact part. Lugs and groove roofs/floors are 45°, and the entry slots
    are open to the bed.
  - The moon's first layer is 142 mm², plus a 3 mm outer brim.
  - No bridges, except the inner dome (≤ 2.98 mm) and the coupon sliver.
  - The skirt wall at the grooves is 1.2 mm (3 lines), with ≥ 1.2 mm under the lowest floor.
  - PETG for the cup and ring, PLA for the moon: the right split.
- **Jig.** Pocket 18.4 × 1.0. Relief r 7.8 × 2.0 (bottom parts ≤ 1.55 mm at r ≤ 7.25; J1 pads inside). The board
  rests on r 7.8–9.0 only, with finger notches under r 8.7–9.0.
- **Doc numbers that match the CAD:**
  - skirt Ø25.3, cup Ø20.8, lugs Ø22.4;
  - opening r 9.0 / 23.69°;
  - LEDs 1.2 mm below;
  - 1.011 / 1.002 / 1.037 (as modelled);
  - escape 0.636 (as modelled);
  - "~7 %" (asin(12.65/25) = 30.4°);
  - ring 0.8 / ID 16.0 / OD 19.8 / 0.4 × 45°;
  - slip 0.15 and GAP_45 0.25.
