# VERIFY: what only the prototype can settle

Every value below was taken from a datasheet, a seller listing or a model. Nobody has measured it yet. Each item
says how to check it and what to change if it is off. Work top to bottom: the first two sections gate the rest.
Tick an item by noting the measured value and the date here.

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
| F5 | LED-board recovery (m6) | Unplug and replug J3 with the lamp on | Light returns within ~3 s | Debug log: `tlc_ok` / MODE1 |
| F6 | Button feel | Press, hold 2 s, auto-repeat | Matches R5–R8 | Tune `DEBOUNCE_MS`, `REPEAT_*` in `lightcore.h` |

## 3. Electrical characterisation

| # | Item | How | Pass | If not |
|---|---|---|---|---|
| E7 | TLC59116 quiescent current (T0) | All outputs off, VLED 4.20 V: current into J3 pin 2 | ≤ 20 mA | Recompute the runtimes and the caps with the measured value |
| E8 | Channel current (REXT 750 Ω) | 1 Ω in series with one white LED, 100 % PWM, CG 0.992 | 25.0 mA ± 8 % | Check R1; update `I_CHANNEL_MA` *and* the test |
| E9 | G/B regulation (M1, F10) | Green mode at max, VLED swept 4.2 → 3.4 V, current through one G die | Holds 12.4 mA down to VLED ≈ 3.55–3.6 V | Accept, or try REXT 910 Ω (20.6 mA) |
| E10 | Charge current | USB in, cell at ~3.7 V: current into J2 | 256 mA ± 10 % | Check R3 3.9 k |
| E11 | USB current draw (M4) | USB meter, charging + 4000 K full | Note the value (expect ~0.5–0.6 A) | Use a ≥ 1 A charger (handoff 02) |
| E12 | Unplug handover (m1) | Scope VSYS while pulling USB at 3.6 V battery | Dip ≤ 0.3 V, no reset | Lower R5 further (4.7 k) |

## 4. Thermal (thermal review §7; thermocouples TC1 board top, TC2 TLC, TC3 PLA skirt, TC4 PLA dome, TC7 cup)

| # | Test | Duration | Pass |
|---|---|---|---|
| T1 | Each mode at max level, 4.20 and 4.15 V: I_VLED cold and after 30 min | 30 min | Within ±8 % of prediction (4000 K full ≈ 182 mA) |
| T2 | Characterisation: derating disabled **on the bench only**, whites at 100 / 150 mA to steady state | ~2 h | Gives the real board → PLA offset. Re-fit `T_DERATE_*` if it differs from ~14 K |
| T3 | Release firmware, 4000 K max, on USB, then on battery | 2 h each | TC3 ≤ 47 °C, TC4 ≤ 45 °C, TC1 ≤ 70 °C, TC2 ≤ 80 °C, TC7 ≤ 60 °C |
| T4 | T3 in a 30–32 °C box | 2 h | TC3 ≤ 50 °C |
| T5a | `pio run -e bench_t_nack` (sensor NACK) at full output | 30 min | Output to 30 % within 3 s; TC3 ≤ 42 °C |
| T5b | `pio run -e bench_t_stuck` (frozen 25 °C reading) | 2 h | Untrusted within 5 min (`T_FROZEN_MS`), current ≤ 110 mA, TC3 ≤ 47 °C |
| T6 | Hardware thermostat: LEDs at 5 %, hot-air on the board underside to LM75B ≥ 60 °C | 10 min | LEDs off within 1 s of OS; resume below 52 °C |
| T7 | Creep: skirt flatness, lug height, skirt OD before and after T3+T4 and 10 × (2 h on / 1 h off) | 1 day | Change ≤ 0.05 mm; bayonet still locks firmly |

## 5. Optical and colour

| # | Item | How | Pass | If not |
|---|---|---|---|---|
| O1 | PLA transmission (T8a) | Print `coupon_litho_wedge` in the production PLA, backlight it per channel in a dark box | Note τ(t). Contrast visible from 0.9 to 2.6 mm | Change the lithophane range in `moonlib.py` (and re-run the optics model) |
| O2 | Total flux (T8b) | 12-direction illuminance at 1 m, 4000 K full, cold | 39 lm ± 20 % | If < 31 lm, PLA absorption is higher than assumed: thin the base wall |
| O3 | Page illuminance (T8c, F6) | Lux meter at 25 / 30 cm, 4000 K full, t = 0 and 30 min | 20–30 lux expected | Feeds the v0.2 reading-LED decision |
| O4 | Uniformity (T8d) | RAW photos at fixed exposure: WW only, CW only, red only, all white | No visible 4- or 2-fold pattern | Raise the diffuser / board depth (optics model) |
| O5 | Flicker (T9) | Photodiode + scope at levels 0, 3, 8, 15 for each mode; slow fades across CG steps | Only 97.6 kHz content; no visible step at a CG change | Adjust the CG hysteresis in `tlc_output()` |
| O6 | Colour per mode (T10, LED bins) | Spectrometer (or a phone colorimeter app as a rough check) | Whites within 3 SDCM / Duv ±0.003; candle Duv ±0.005 | Put the measured xy and lumens into `LED` in `gen_modes.py` and regenerate |
| O7 | Green chromaticity | Same as O6, green only | xy near (0.17, 0.70) | Update `LED["G"]` (520 nm usually sits greener) |

## 6. Mechanical (from the parts' `VERIFY` dicts)

| # | Item | Part | Check |
|---|---|---|---|
| M1 | Gooseneck end thread M10×1, nut 14 AF × 3.0 mm | `moon_base`, `pack_front` | Calipers on the delivered gooseneck. Change `NUT_AF`, `NUT_T`, `NECK_THREAD_D` in `moonlib.py` / `packlib.py` |
| M2 | Neck socket 9.3 mm for self-tapping into PETG | `pack_front` | Print `coupon_fit` first |
| M3 | Printed slip fit 0.15 mm radial | all | `coupon_fit` |
| M4 | Bayonet: lugs enter, turn 30°, pull down onto a 1.0 mm disc | `moon_shell`, `moon_base` | `coupon_bayonet` |
| M5 | Ring preload: board must not rattle with the moon locked | `moon_ring` | Add a 0.2 mm shim ring if it rattles |
| M6 | LED board thickness 1.0 mm as ordered | `moon_base` | Calipers on the delivered board |
| M7 | Battery 64.0 × 35.5 × 5.3 mm (listing) | `pack_back` | Calipers on the delivered cell; bay is 36.0 × 64.5 × 5.6 + 0.6 swell |
| M8 | USB-C receptacle centre 1.63 mm above the PCB; PCM12 knob 0.9 mm above, 1.0 mm past the edge; PH plug ≤ 5.2 mm tall | `pack_front` | Calipers on the assembled main board before printing the shell |
| M9 | Clip force ~5 N at 3 mm | `pack_clip` | Holds on a hardback and a paperback without marking them |
| M10 | Button caps 7.0 mm in 7.4 mm holes | `button_caps` | Slide freely; sand if tight |
| M11 | Lithophane 0.9–2.6 mm reads well at 0.12 mm layers | `moon_shell` | First print, lit and unlit |
