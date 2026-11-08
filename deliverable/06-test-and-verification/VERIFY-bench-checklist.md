# VERIFY: what only the prototype can settle

Every value below was taken from a datasheet, a seller listing or a model. Nobody has measured it yet. Each item
says how to check it and what to change if it is off. Work top to bottom: the first two sections gate the rest.
Tick an item by noting the measured value and the date here.

SPICE predictions (`docs/verification/spice-report_main-v0.1_led-v0.2_rev2.md` and `.pdf`, rev 2, 2026-11-08) for several items: E12 is predicted to fail its
0.3 V limit (0.64 V dip for ~21 ms; R5 4.7k shortens it, does not reduce it); E13's hot-plug step is predicted to
reset the MCU at 3.5 V (VSYS ~2.3 V; the step has been removed, D2), the power-on and empty-sleep steps to pass (VLED 10-90 % in ~1.0 ms, VSYS dip
~12 mV); E15 passes on a 5.0 V source (4.00 V) but not at 4.75 V through a 0.2 Ω cable with F1 at its 0.2 Ω maximum (3.71 V). Record the measured value
beside the prediction, and update `sim/` with it.

## 1. Before the first power-up (bench, meter, no battery)

| # | Item | How | Pass | If not |
|---|---|---|---|---|
| E1 | Battery lead polarity | Meter on the cell's JST-PH plug: red = J2 pin 1 (silk "+") | + on pin 1 | Re-pin the plug (PH crimps lift out with a needle). Never "try it": with USB present a reversed cell is not blocked (round1 m2) |
| E2 | SW1 ON direction (N5) | No battery; bench supply 3.7 V, 100 mA limit, on J2 (+ = pin 1). Slide SW1 both ways and meter TP3 (VSYS) to TP4 (GND) | One direction gives VSYS ≈ 3.7 V | Mark ON on the pack with a dot. If the "ON" side is the awkward one, flip `pack_front` text, not the PCB |
| E3 | Supply sequencing | Bench 3.7 V on J2 (current limit 300 mA), switch ON, MCU flashed, nothing on J3 | I < 5 mA; VLED (J3 pin 2) = VSYS once the firmware runs, 0 V while the MCU is held in reset | Check Q2/Q4 orientation and R6/R12 |
| E4 | Off current (R17) | Switch OFF, 4.0 V on J2, µA meter in series | ≤ 10 µA | Lift Q2 / D3 to find the leak |
| E5 | 10 µF 0805 DC bias (N3) | LCR meter at 1 kHz with 4 V bias, or the charger ripple on a scope | ≥ 4.7 µF effective | Replace C1/C2 with 1206 or a 25 V 0805 |
| E6 | D1 land pattern (N4) | Visual after reflow: fillets on both terminals | Solder fillet both ends | Hand-touch with the iron; widen the pads in v0.2 |

## 2. Firmware bring-up (handoff 04)

| # | Item | How | Pass | If not |
|---|---|---|---|---|
| F1 | Fuses written (FW-09) | `pio run -e attiny3216 -t fuses`, then flash the debug build and read the boot line | No "BOD OFF" line | Re-run the fuses target; check the programmer wiring |
| F2 | Silicon revision (FW-12) | Debug build prints `SYSCFG.REVID` (add one line), or read it with the programmer | Any revision: the RTC is enabled for the PIT anyway | — |
| F3 | VDD reading (m-9, FW-08) | Debug serial `V=` vs a meter on VSYS at 3.5, 3.8, 4.1 V (bench supply on J2) | Within ±50 mV | Add a calibration factor (measured / read) to `config.h` and scale `vdd_mv()` |
| F4 | Empty sleep and resume | Bench supply on J2 down to 3.25 V for 6 s → fades out and sleeps. Then measure the sleep current. Raise it to 3.8 V or plug in USB | Sleep ≤ 30 µA (LED board unpowered); wakes in 3–5 s | Check PB2/Q4; check the PIT wake (F2) |
| F5 | LED-board recovery (m6) | Unplug and replug J3 with the lamp on | Light returns within ~3 s | Debug log: `lp=` must return to `1C` and `ts=` to 1 |
| F6 | Button feel | Press, hold 2 s, auto-repeat | Matches R5–R8 | Tune `DEBOUNCE_MS`, `REPEAT_*` in `lightcore.h` |

## 3. Electrical characterisation

| # | Item | How | Pass | If not |
|---|---|---|---|---|
| E7 | LP5012 + MCP9800 supply current (LED board v0.2) | VLED 4.20 V, current into J3 pin 2: (a) all outputs at 0 for > 30 ms (power save), (b) one output on | (a) ≤ 0.45 mA (LP5012 ≤ 10 µA + MCP9800 ≤ 0.4 mA max, 0.2 mA typ; the idle bus draws nothing through the 3.3 k pull-ups), (b) ≤ 6 mA + the LED current | Recompute the runtimes with the measured value |
| E8 | Channel current (RIREF 2.94 kΩ) and colour polarity | 1 Ω in series with one white LED: colour 255 × brightness 255, then colour 0 × brightness 255 (the datasheet's OUTx_COLOR tables say FFh = 0 %, contradicting the rest of it: round3 R3-F1) | 25.0 mA ± 5 % at colour 255, 0 mA at colour 0 | Check R1 (0402 on the LED board's bottom); update `I_CHANNEL_MA` *and* the tests |
| E9 | G/B regulation (M1, F10; v0.2) | First measure the received G and B dies' V_F at 25 mA, **and one 2700 K and one 5000 K white** (SPICE D4: worst-case whites start to dim just below the 3.45 V cap; if a white reads > ~2.85 V at 25 mA, raise `VBAT_LOW_MV` to 3500) (bench supply + 1 Ω, D9 on a spare board or before reflow). Then Green mode at max, VLED swept 4.2 → 3.4 V; scope across 1 Ω in series with the G die and read the **peak**, not the average (PWM). The LP5012 has no per-channel current step, so G/B always run at the 25 mA peak | Peak 25 mA held down to VLED ≈ V_F(measured) + 0.35–0.45 V (typical die ≈ 3.65 V; a maximum-V_F die (~3.7 V at 25 mA) needs ~4.05–4.15 V, i.e. it is never fully regulated: round3 R3-E3) | Accept (G/B dim gracefully below that), or RIREF 3.65 kΩ (20 mA for every channel) |
| E10 | Charge current | USB in, cell at ~3.7 V: current into J2 | 256 mA ± 10 % | Check R3 3.9 k |
| E11 | USB current draw (M4) | USB meter, charging + 4000 K full | Note the value (expect ~0.5–0.6 A) | Use a ≥ 1 A charger (handoff 02) |
| E12 | Unplug handover (m1) | Scope VSYS while pulling USB at 3.6 V battery | Dip ≤ 0.3 V, no reset | Lower R5 further (4.7 k) |
| E13 | Q4 soft turn-on (round2 R2-E1) | Scope VSYS (TP3) and VLED (TP7) at power-on and on the empty-sleep wake, at 3.5 V battery. J3 is not hot-plugged: it is mated once at assembly with SW1 off (SPICE D2, Matt 2026-11-08) | VLED ramps over ~1–2 ms; VSYS dips ≤ 0.2 V; no reset | Raise C8 (220 nF) or add 47 µF bulk on VSYS |
| E14 | F1 PTC when warm (round2 R2-E3) | USB in, charging, 4000 K full for 30 min, pack closed; contact thermometer on F1 | No trip; F1 ≤ 60 °C | Move F1 away from U1/D3 in v0.2 |
| E15 | VSYS on USB (round2 note) | USB in from a 5.0 V, ≥ 1 A USB-C charger, 4000 K full: meter TP3; then let the lamp reach empty sleep and plug the same charger in (SPICE D3, Matt 2026-11-08: the limit applies to a 5.0 V source; weak sources are expected to read lower) | VSYS ≥ 3.9 V on the 5.0 V source; wakes from empty sleep on USB. Informational: repeat the wake check on the weakest charger Matt actually uses (laptop port, hub); a late wake there is what triggers the remedy (D3 option B) | Lower `VBAT_RESUME_MV` to 3600 in `lightcore.h` |
| E16 | LP5012 WQFN-20 joints (LED board v0.2) | After both reflows: diode-test every LED from the exposed end of its cathode pad (handoff 05 §2.3; the vias are tented); then power up and read DEVICE_CONFIG1 (debug log) | Every LED glows at the diode test and lights in its mode at first light; the read-back is 0x1C (`lp=1C`) | Dark at the diode test = LED reversed or open on top. Dark only at first light = an open OUTx joint under U1: reflow with flux. No I2C answer at all (`lp=--`) = EP (GND), VCC or SDA/SCL joint |
| E17 | Thermostat path (v0.2) | Flash `bench_tstat_low` (TSET 30 °C / THYST 28 °C, debug log on; **bench only**). At room temperature the lamp lights; warm U2 with a fingertip or a hair dryer until `T=` passes 30 °C | ALERT pulls EN low within ~0.5 s: all LEDs off, `lp=--`. Below 28 °C the firmware re-initialises the LP5012 and the light returns. **Reflash the release build afterwards** | Check R2 (0402 on the TOP face, NE gap) and U2 pin 3 |
| E18 | LP5012 VCAP and IREF ground (round3 R3-E2: their ground returns to the LP5012's exposed pad are ~22–26 mm of pour) | 4000 K at full, steady. AC-coupled scope probe on C4 (VCAP, bottom face) with a short ground spring to C4's GND pad; then E8's 1 Ω current reading over 1 min | VCAP ripple < 50 mV p-p with no bursts; channel current steady within ±1 % | Next board revision: EP vias + a short GND jumper for C4/R1 (layout note in round3.md) |

## 4. Thermal (thermal review §7; thermocouples TC1 board top, TC2 LP5012, TC3 PLA skirt, TC4 PLA dome, TC7 cup)

| # | Test | Duration | Pass |
|---|---|---|---|
| T1 | Each mode at max level, 4.20 and 4.15 V: I_VLED cold and after 30 min | 30 min | Within ±8 % of prediction (4000 K full ≈ 178 mA) |
| T2 | Characterisation: derating disabled **on the bench only**, whites at 100 / 150 mA to steady state | ~2 h | Gives the real board → PLA offset. Re-fit `T_DERATE_*` if it differs from ~14 K |
| T3 | Release firmware, 4000 K max, on USB, then on battery. TC2 directly on U1 (centre of the bottom face); log the debug `T=` alongside for 15 min at steady state (frozen-code check, R3-F6) | 2 h each | TC3 ≤ 47 °C, TC4 ≤ 45 °C, TC1 ≤ 70 °C, TC2 ≤ 80 °C, TC7 ≤ 60 °C. Record TC2 − `T=` (the LP5012 runs hotter than the sensor: R3-E4) for T2's re-fit; the light must not "breathe" between 178 and 110 mA |
| T4 | T3 in a 30–32 °C box | 2 h | TC3 ≤ 50 °C |
| T5a | `pio run -e bench_t_nack` (sensor NACK) at full output | 30 min | Output to 30 % within 3 s; TC3 ≤ 42 °C |
| T5b | `pio run -e bench_t_stuck` (frozen 25 °C reading) | 2 h | Untrusted within 5 min (`T_FROZEN_MS`), current ≤ 110 mA, TC3 ≤ 47 °C |
| T6 | Hardware thermostat: LEDs at 5 %, hot-air on the board underside to the MCP9800 ≥ 60 °C | 10 min | LEDs off within 1 s of ALERT (LP5012 EN low); resume below 52 °C after the firmware re-init |
| T7 | Creep: skirt flatness, lug height, skirt OD before and after T3+T4 and 10 × (2 h on / 1 h off) | 1 day | Change ≤ 0.05 mm; bayonet still locks firmly |

## 5. Optical and colour

| # | Item | How | Pass | If not |
|---|---|---|---|---|
| O1 | PLA transmission (T8a) | Print `coupon_litho_wedge` in the production PLA, backlight it per channel in a dark box | Note τ(t). Contrast visible from 0.9 to 2.6 mm | Change the lithophane range in `moonlib.py` (and re-run the optics model) |
| O2 | Total flux (T8b) | 12-direction illuminance at 1 m, 4000 K full, cold | ≈ 37 lm ± 20 % (61 lm of LED flux × 0.61 escape, v0.2 head, head_v02.txt) | If < 30 lm, PLA absorption is higher than assumed: thin the base wall |
| O3 | Page illuminance (T8c, F6) | Lux meter at 25 / 30 cm, 4000 K full, t = 0 and 30 min | 20–30 lux expected | Feeds the next revision's reading-LED decision |
| O4 | Uniformity (T8d) | RAW photos at fixed exposure: WW only, CW only, red only, all white | No visible 4-fold pattern (model max/min 1.028 one white / 1.021 all white / 1.037 RGB, docs/design/optics/head_v02.txt). The 45° collar band near the base (θ 30–45° from the bottom pole) reads darker and plain by design (B8: smooth and 2.6–3.5 mm thick) | Check the LED depth: emitters 1.2 mm below the opening (moon_shell B13). Deeper shades the low wall |
| O5 | Flicker (T9; LP5012) | Photodiode + scope at levels 0, 3, 8, 15 for each mode; slow fades across brightness-register steps; phone slow-motion video | Content at the 29 kHz PWM and its ~3.6 kHz dither pattern only; no visible step when `lp_brightness()` changes | Turn PWM dithering off (`LP_CONFIG1` b2 = 0: 9-bit) or widen the hysteresis in `lp_brightness()` |
| O6 | Colour per mode (T10, LED bins) | Spectrometer (or a phone colorimeter app as a rough check) | Whites within 3 SDCM / Duv ±0.003; candle Duv ±0.005 | Put the measured xy and lumens into `LED` in `gen_modes.py` and regenerate |
| O7 | Green chromaticity | Same as O6, green only | xy near (0.17, 0.70) | Update `LED["G"]` (520 nm usually sits greener) |

## 6. Mechanical (from the parts' `VERIFY` dicts)

| # | Item | Part | Check |
|---|---|---|---|
| M1 | Gooseneck end thread M10×1, nut 14 AF × 3.0 mm; moon-end thread length ≥ 9 mm (jam nut + washer + floor + socket nut); any shoulder ≥ 12 mm on the end | `moon_base`, `pack_front` | Calipers on the delivered gooseneck. Change `NUT_AF`, `NUT_T`, `NECK_THREAD_D` in `moonlib.py` / `packlib.py`. A shoulder ≥ 12 mm can replace the jam nut (B16) |
| M12 | Thread protrusion in the moon base (round2 R2-D3) | `moon_base` | With both nuts tight, the thread must not stand more than 0.5 mm above the socket nut's top; the board's underside is 4.5 mm above. Cut/file it to length **before** the cable goes in (handoff 05 §3) |
| M13 | Battery lead path (round2 R2-D18) | `pack_back`, main board slot | Lead exit end and length on the real cell. The plug passes the 6.4 × 5.0 slot; the slack must lie flat in the bay's end gap without crossing the screw heads. If it doesn't, Claude adds a lead channel to `pack_back` |
| M14 | LED-board jig (round2 R2-D12) | `jig_led_board` | The board drops in flush, and the bottom parts don't touch the relief floor |
| M2 | Neck socket 9.3 mm for self-tapping into PETG | `pack_front` | Print `coupon_fit` first |
| M3 | Printed slip fit 0.15 mm radial | all | `coupon_fit` |
| M4 | Bayonet (v0.2, inside out; round 3): the skirt slides over the cup, the lugs enter its slots, a **clockwise** 30° turn (seen from the top) pulls the moon down onto the PETG ring, preloading it by `LOCK_OFFSET` 0.15 mm + (disc − 1.0); the ring's roll over the cup's land is the spring | `moon_shell`, `moon_base` | `coupon_bayonet_cup` (PETG) + `coupon_bayonet_skirt` (the moon's PLA), with 18 mm discs 0.9, 1.0 and 1.1 mm thick. Pass: locks by hand without forcing, no whitening at the groove ends, no rattle. Tune `LOCK_OFFSET` in `moonlib.py` (lower = looser) in 0.05 mm steps and reprint both halves |
| M5 | Ring preload: board must not rattle with the moon locked (ring 0.8 mm, ID 16.4, at 0.12 mm layers; clamp cone on its 45° chamfer) | `moon_ring` | Tune `LOCK_OFFSET` (M4). No shims: they add rigid interference on top of the spring's travel |
| M6 | LED board thickness 1.0 mm as ordered | `moon_base` | Calipers on the delivered board |
| M7 | Battery 64.0 × 35.5 × 5.3 mm (listing) | `pack_back` | Calipers on the delivered cell; bay is 36.0 × 64.5 × 5.6 + 0.6 swell |
| M8 | USB-C receptacle centre 1.63 mm above the PCB; PCM12 knob 0.9 mm above, 1.0 mm past the edge; J2 header 5.5 mm tall (JST), under a 0.8 mm face pocket; your USB-C cables seat fully in the 13.4 × 7.6 window | `pack_front` | Calipers on the assembled main board before printing the shell; try your cables in the printed shell |
| M9 | Clip force ~5 N at 3 mm | `pack_clip` | Holds on a hardback and a paperback without marking them |
| M10 | Button caps 7.0 mm in 7.4 mm holes | `button_caps` | Slide freely; sand if tight |
| M11 | Lithophane 0.9–2.6 mm reads well at 0.12 mm layers | `moon_shell` | First print, lit and unlit |
