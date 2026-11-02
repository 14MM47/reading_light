# Verification round 1: findings and dispositions

Date 2026-11-02. Four independent reviewers worked from the design files, the generated KiCad outputs and the
datasheets. None of them edited the repo; Claude applied the fixes afterwards. Full reports:

| Reviewer | Brief | Report |
|---|---|---|
| Electrical | every net, part and rating against its datasheet (power path, charger, FET orientation, LED headroom, I²C, leakage) | [round1/electrical.md](round1/electrical.md) |
| Adversarial | break it: misuse, faults, LiPo safety, mechanical fit, single points of failure | [round1/adversarial.md](round1/adversarial.md) |
| Firmware | code review + host tests against the hardware and the TLC59116 / LM75B / ATtiny datasheets | [round1/firmware.md](round1/firmware.md) |
| Thermal + optical | heat in the moon head vs PLA, sphere uniformity, illuminance, colour recipes | [round1/thermal_optical.md](round1/thermal_optical.md) |

The datasheet extracts the reviewers cite (`.../scratchpad/ds/*.txt`) were session working files. The values that
matter are in [`docs/datasheets/KEYSPECS.md`](../datasheets/KEYSPECS.md), with page references.

**Result:** 4 blockers and 21 majors raised. All blockers are fixed. Every major is either fixed, or mitigated with
the residual risk written down. Four items are Matt's call (§5).

Dispositions: **FIXED** (changed in the design, then rebuilt and checked) · **MITIGATED** (risk reduced, residual
stated) · **ACCEPTED** (known limitation, documented) · **VERIFY** (only the prototype can settle it; see
[VERIFY.md](VERIFY.md)) · **MATT** (owner decision, recommendation given).

## 1. Electrical review

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| B1 | BLOCKER | `board_map.h` was stale: 15 of 16 outputs mapped to the wrong LED group | **FIXED.** `hardware/build.py led-board` now writes `firmware/include/board_map.h` from the netlist. `tests/test_consistency.py` fails if they differ |
| M1 | MAJOR | Green and blue (VF 3.2–3.6 V) + TLC knee need VLED ≥ 3.65–3.9 V; on battery they sag | **MITIGATED.** The Green and Blue modes run at half current (12.4 mA, lower VF and knee), so they regulate down to about 3.6 V of battery. The mixed whites use only a little G/B, and their colour drifts slightly at low battery: **ACCEPTED**, documented in electronics.md §2. A 5 V boost for the anodes is listed for v0.2 |
| M2 | MAJOR | The MCU could not unpower the LED board; "empty" sleep left the TLC59116 drawing up to 25–37 mA | **FIXED.** Q4 (DMG2305UX) switches VSYS → VLED, gate driven by PB2 and pulled up by R12 100 k (off in reset). Firmware cuts it in empty sleep. The I²C pull-ups moved to VLED so the off board is never back-fed |
| M3 | MAJOR | J4 pin 1 = VSYS: a programmer that supplies VCC back-feeds the LiPo uncontrolled | **FIXED.** J4.1 is now VREF through R11 1 k (sense only). Silk and handoff 04 say "never power the board from the programmer" |
| M4 | MAJOR | USB draw (417 mA charge + lamp through D3) can exceed 500 mA default USB power | **FIXED / MITIGATED.** R3 3.9 k → 256 mA charge (0.21 C, also less charger heat, m4). Handoff 02 asks for a ≥ 1 A USB-C charger. The lamp load on USB is still additive: **ACCEPTED** (Rd-only sink, no PD negotiation) |
| m1 | MINOR | Slow USB-unplug handover (R5 100 k τ ≈ 0.7 s) → brown-out | **FIXED.** R5 10 k (τ ≈ 70 ms); firmware empty-hold 5 s ≫ handover |
| m2 | MINOR | Reverse battery not blocked while USB is present (Q3 biased by the charger) | **ACCEPTED.** Nothing is destroyed: about 42 mA precharge into the reversed cell, stopped by its PCM. The JST PH is keyed, and handoff 05 adds a polarity check with a meter before the first plug-in. v0.2: low-side N-FET reverse protection |
| m3 | MINOR | TVS SMF5.0A clamps (~9 V) above MCP73831 VDD abs max 7 V | **MITIGATED.** F1 PTC 0.75 A hold (MF-MSMF075-2) ahead of the TVS: a sustained over-voltage makes the TVS conduct and trips the PTC. Fast transients above 7 V remain possible from non-compliant sources: **ACCEPTED** for a USB-C 5 V-only sink |
| m4 | MINOR | Charger dissipation up to 1.2 W in SOT-23-5 next to the cell; no NTC | **MITIGATED.** 256 mA charge (≤ 0.5 W). U1 sits on the GND pour (both layers), and the pouch is separated by tape plus a 1.6 mm air gap (pack CAD). No NTC: charge at room temperature only (user note). v0.2: MCP73833 with NTC |
| m5 | MINOR | Würth RGB 27 mA (worst tolerance) is allowed only to ~55 °C ambient | **MITIGATED.** Firmware derates from 45 °C board temperature (5 % at 58 °C), and the LM75B thermostat cuts the driver at 60 °C. Single-colour G/B run at 12.4 mA |
| m6 | MINOR | TLC RESET hard-tied to VLED: a brown-out between 0.2 and 2.5 V can leave the driver undefined | **FIXED.** RESET is now driven by the LM75B OS (thermostat) with R2 10 k pull-up. Firmware re-initialises on any MODE1 mismatch. After 4 failed inits it power-cycles the LED board through Q4 |
| m7 | MINOR | Battery "+" silk hidden under the J2 housing | **FIXED.** "+" / "−" now sit outside the housing at the board edge, plus a "BATT" label |
| m8 | MINOR | MCU cannot see VBUS or charge state | **ACCEPTED** for v0.1 (the red charge LED shows charging). v0.2: VBUS divider to a free ADC pin |
| N1–N12 | NOTE | Inrush, Q1 Vgs on ESD, 0805 DC-bias, D1 land pattern, SW1 ON direction, UART back-power, no-battery LED flicker, cable LC, LED board thickness, ERC lib mismatch, J3 VLED on a Qwiic pinout, J2 polarity | N9 **FIXED** (board files now 1.0 mm). N3, N4, N5 → **VERIFY**. N6, N7, N11 → handoffs/user notes. The rest need no action |

## 2. Adversarial review

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| B-1 | BLOCKER | After an empty-sleep reset the LM75B stayed in shutdown: derating silently frozen | **FIXED.** Firmware patch, and now the LED board is fully power-cycled by Q4 anyway. The LM75B is reconfigured at every init. A frozen reading under load is detected (`T_FROZEN_MS`) and the cap drops to 110 mA |
| B-2 | BLOCKER | M2 screw heads on the PCB back face press into the pouch | **FIXED.** Pack stack gives 1.6 mm between the PCB bottom and the pouch top (pan head 1.3 mm), plus 0.6 mm swell space. Handoff 05: Kapton over the pouch; J4 not populated (pads only) |
| B-3 | BLOCKER | J2 face 0.5 mm from the board edge: the PH plug cannot fit, battery leads pinched | **FIXED.** J2 rotated so the plug lies flat on the board (keep-out under it). The leads drop through a 3.0 × 2.8 mm slot to the cell behind the PCB |
| M-1 | MAJOR | One I²C bus + cable for sensor and driver; no watchdog; a hang latches LEDs on without thermal control | **FIXED.** Hardware thermostat (LM75B OS → TLC RESET, Tos 60 / Thyst 52 °C) works with no MCU or bus. A 2 s WDT, I²C bus recovery, MODE1 check every 1 s, and a 110 mA cap without a trusted sensor |
| M-2 | MAJOR | Derating 50/65/75 °C let the PLA skirt (the board clamp) sit at its HDT | **FIXED.** Derating 45/52/58 °C. A 0.6 mm PETG clamp ring (`moon_ring`) keeps the PLA off the board |
| M-3 | MAJOR | Empty sleep left the TLC powered: cell drained to PCM cut-off | **FIXED** (Q4, as M2) |
| M-4 | MAJOR | No charge temperature qualification (no NTC, no timer) | **MITIGATED** (see m4): 0.21 C charge, charger isolated from the pouch, user note "charge at room temperature". **MATT** for v0.2 (NTC charger + a 10 k NTC cell) |
| M-5 | MAJOR | No VBUS over-voltage protection | **MITIGATED** (see m3): the PTC + TVS combination trips on a sustained fault. A real OVP (e.g. TPS2595) is a v0.2 option |
| M-6 | MAJOR | No over-current protection on USB→D3→VSYS→cable | **MITIGATED.** F1 PTC (0.75 A hold, 1.5 A trip) limits the USB side. Battery side: the cell PCM (2–3 A, µs short-circuit cut) is the backstop. The neck cable is protected mechanically (M-7) |
| M-7 | MAJOR | No abrasion protection or strain relief for the cable in the neck, at the LED pads or at the JST-SH | **FIXED (process).** Handoff 05: PTFE/silicone sleeve through the gooseneck, heat-shrink over the thread ends, a glue fillet over the LED-board pads, and a cable-tie anchor before the JST-SH |
| m-1 | MINOR | Reversed cell with USB present not blocked | **ACCEPTED** (as electrical m2) |
| m-2 | MINOR | USB unplug brown-out | **FIXED** (R5 10 k) |
| m-3 | MINOR | `I_CHANNEL_MA` 30.2 vs 25.0 mA hardware | **FIXED.** 25.0 mA, and a test ties it to REXT in the LED board design |
| m-4 | MINOR | IREF / PWM write order flash | **FIXED** (ordered writes: gain up → PWM first, gain down → IREF first) |
| m-5 | MINOR | No read-back, plausibility check or bus recovery; `tlc_ok` never drops | **FIXED** |
| m-6 | MINOR | Metal neck within ~1–2 mm of the TLC pins; no ESD parts on SDA/SCL/buttons | **ACCEPTED.** The neck is sleeved (insulated), and the buttons sit behind PETG caps. v0.2: a TVS array on SDA/SCL at J3 |
| m-7 | MINOR | Thread-locker on PETG crazes it; bayonet unlock direction unscrews the base cup | **FIXED (process).** Handoff 05 says no anaerobic thread-locker: use the nut plus a drop of CA, or nothing. Hold the base cup when twisting the moon off |
| m-8 | MINOR | Clip and back plate not designed; enclosure must not crush a swelling pouch | **FIXED / ACCEPTED.** `pack_back` and `pack_clip` are designed, and the pouch is not structural: the PCB hangs from the front shell, and the clip loads the back plate. The bay has 0.6 mm swell space, enough for ageing. The plate is held by two hook tabs and two M2 screws, so it will not give way: a pouch that swells beyond 0.6 mm is a failed cell (user note: stop using it and replace it) |
| m-9 | MINOR | VDD measurement via INT1V1 is ±2–5 % (±70 mV) | **VERIFY.** Handoff 04 has a one-point check against a meter. The thresholds (3.45 / 3.30 V) sit above the PCM cut-off with margin for this error |

## 3. Firmware review

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| FW-01 | BLOCKER | board_map.h stale | **FIXED** (as B1) |
| FW-02 | BLOCKER | `blink_until` wrap: 5 Hz strobe after 24.9 days; re-fade at 49.7 days | **FIXED** (elapsed-time arithmetic). Tests `no_strobe_after_24_8_days_on`, `no_refade_after_49_7_days_on` |
| FW-03 | MAJOR | Recipes computed for the wrong RGB LED | **FIXED.** `gen_modes.py` uses Würth 150141M173100 and Bridgelux data at 25 mA. A test checks that night modes light only red/warm outputs on the real board map |
| FW-04 | MAJOR | `I_CHANNEL_MA` mismatch | **FIXED** (as m-3) |
| FW-05 | MAJOR | LM75B left in shutdown | **FIXED** (as B-1) |
| FW-06 | MAJOR | No watchdog | **FIXED** (2 s WDT, kept alive in the PIT sleep too) |
| FW-07 | MAJOR | TLC errors ignored | **FIXED** (checked writes, MODE1 poll, re-init, power-cycle) |
| FW-08 | MAJOR | VDD first-conversion error; resume trusts one sample | **FIXED.** First conversion discarded; resume needs 3 consecutive good readings. Bench check in VERIFY |
| FW-09 | MAJOR | Fuses (BOD 2.6 V, EESAVE) never programmed by `upload` | **FIXED (process).** Handoff 04 runs `pio run -e attiny3216 -t fuses` once per chip. The debug build warns at boot if BOD is off |
| FW-10 | MAJOR | Empty sleep leaves the LED board powered | **FIXED** (Q4) |
| FW-11 | MINOR | IREF before PWM flash | **FIXED** |
| FW-12 | MINOR | PIT with RTC disabled (tinyAVR 1-series erratum) | **FIXED.** RTC enabled before the PIT. Bench check: USB resume from empty |
| FW-13 | MINOR | `static last_slew` shared across instances | **FIXED** (moved into `core_t`; test `thermal_slew_independent_per_instance`) |
| FW-14 | MINOR | `powf` in the 1 ms tick (1.34 ms while slewing) | **ACCEPTED.** All timing is elapsed-based, so a long tick only delays, never mis-times. The slew is short |
| FW-15 | MINOR | No I²C bus recovery | **FIXED** |
| FW-16 | MINOR | Unsequenced `Wire.read()`; no plausibility check | **FIXED** |
| FW-17 | MINOR | Uninitialised `t` | **FIXED** |
| FW-18 | MINOR | `-w` hid warnings | **FIXED** (`-Wall -Wextra`; the build is warning-free in project code) |
| FW-19 | MINOR | Soft-orange night mode uses the 2700 K white (has some blue/green) | **MATT.** Recommendation: keep it. 30 % of its luminance is warm white, which makes it read as orange rather than red. Pure-red "Red night light" is the strict no-blue mode, next in the cycle |

## 4. Thermal and optical review

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| F1 | BLOCKER | PLA skirt clamping the board would sit at 50–56 °C (PLA softening) | **FIXED.** Derating 45/52/58 °C, PETG clamp ring, PLA ≥ 0.5 mm air gap from the board. With the ring, the PLA runs about 14 K below the board (review §4.4: 48 °C PLA at a 63 °C board, 200 mA steady). Derating holds the board ≤ 52 °C, so the PLA stays at about 40–45 °C in a 25 °C room. The silicone gap pad option (−3 K more) is not adopted for v0.1. Thermal bench plan in VERIFY (T1–T8) |
| F2 | MAJOR | Budget ignored the TLC59116 (0.3–0.4 W) | **FIXED.** Budget redone in electronics.md: 200 mA cap only with a trusted sensor, 110 mA otherwise; derating holds the board ≤ 52 °C in steady state |
| F3 | MAJOR | `I_CHANNEL_MA` mismatch | **FIXED** |
| F4 | MAJOR | No sensor-independent limit | **FIXED.** Hardware thermostat + untrusted cap (implausible, stale or frozen reading = untrusted). Tests cover each case |
| F5 | MAJOR | PLA skirt is the clamp | **FIXED** (PETG ring, `moon_ring.py`, claims in `moon_shell`/`moon_base`) |
| F6 | MAJOR | Reading illuminance only 15–30 lux at 25–30 cm (reading needs 100–500) | **MATT** (§5.1). The moon is a beautiful ambient / night light but not a task light within its thermal budget |
| F7 | MAJOR | Recipes used the wrong RGB data | **FIXED** (as FW-03); Candle 1900 K now lands on the locus by construction |
| F8 | MINOR | Optics script vs as-built geometry; RGB-only uniformity 1.06–1.14 | **ACCEPTED.** Whites ≤ 1.04 (the claim that matters). The RGB-only claim is corrected to "≤ 1.15" in the PLAN |
| F9 | MINOR | Night-level resolution: CG 0.083 (2.1 mA) below the 5 mA minimum; minor channels 0–2 counts | **FIXED / ACCEPTED.** Current-gain steps limited to the datasheet ranges (8.3 / 12.4 / 24.8 mA). Night red max raised to level 15. Soft orange's warm-white share quantises at low levels and those levels render red-orange: **ACCEPTED** (v0.2: a dedicated amber LED) |
| F10 | MINOR | G/B trim fades below ~3.7 V VLED | **ACCEPTED / MITIGATED** (as M1) |
| F11 | NOTE | 97.6 kHz PWM flicker-free (IEEE 1789) | No action. Group PWM (190 Hz) stays unused (LDR = 10) |
| F12 | NOTE | Junction temperatures have big margins | No action |

## 5. Decisions for Matt

1. **Reading brightness (F6).** At full 4000 K the page gets about 20–30 lux at 25–30 cm. Comfortable reading needs
   100–500 lux, and the thermal budget inside a PLA moon cannot close that gap. Options:
   **(a, recommended)** v0.1 as designed: a moon lamp that is great for ambience and night reading in a dark room,
   not for a full evening's reading. **(b)** v0.2 adds a small downward reading LED (1 W warm white, its own driver
   channel) in a PETG collar under the moon, aimed at the page. That gives about 150–300 lux, and the heat sits in the
   collar, not the moon. The LED board has 2 spare TLC outputs; one 25 mA output is too weak, so (b) needs its own
   driver.
2. **Charge safety (M-4).** v0.1 has no cell-temperature qualification. Recommendation for v0.2: MCP73833/4 with a
   10 k NTC cell.
3. **FW-19 soft orange** keeps 30 % warm white (recommended), or becomes red + a trace of warm white.
4. **Colour drift of G/B at low battery (M1)** accepted for v0.1, or a 5 V boost for the RGB anodes in v0.2.

## 6. Re-check after the fixes

- `python3 hardware/build.py main-board` and `led-board`: ERC 0 / DRC 0 errors / 0 unconnected / 0 schematic parity
  (silk warnings only, listed in the fab notes).
- `pio test -e native`: 25/25 pass. `pio run`: attiny3216 and attiny3216_debug build, project code warning-free.
- `python3 -m pytest tests`: board map, pins, REXT ↔ `I_CHANNEL_MA`, LED group counts all consistent.
- `python cad/tools/export_print.py`: all 10 parts PASS the 3dprint checks and are exported to `print/`.
