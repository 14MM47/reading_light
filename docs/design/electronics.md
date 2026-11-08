# Electronics design notes and calculations

Source of truth: `hardware/main-board/design.py`, `hardware/led-board/design.py`, `hardware/parts.py`.
Datasheet extracts with page references: `docs/datasheets/KEYSPECS.md`. Review findings and their dispositions:
`docs/verification/`.

## 1. Power path (main board)

| State | Q1 load-share (G = VBUS) | D3 S1J | Q2 load switch | Q3 rev-batt | VSYS |
|---|---|---|---|---|---|
| Battery only, switch ON | Vgs = −VBAT → on | reverse-biased (nA) | on | on (Vgs = −VBAT) | VBAT − I·(Rq1+Rq2+Rq3) |
| Battery only, switch OFF | on | reverse (nA) | off | on | 0 (VSYS_RAW = VBAT, isolated by Q2) |
| USB + battery, ON | Vgs ≈ VBUS − VSYS_RAW ≈ +0.85 V → off | forward, VSYS ≈ 5.0 − F1 − 0.85 ≈ 3.9–4.1 V | on | on | ≈ 3.9–4.1 V from USB (F1 PTC drop 0.03–0.1 V + D3); charger sees only the cell → terminates normally |
| USB, switch OFF | off | forward | off | on | 0; charger runs (red LED) |
| Battery reversed, no USB | — | — | — | Vgs ≈ 0 → off, body diode reverse → blocks | 0 |
| Battery reversed + USB | — | — | — | charger biases Q3 on: ~42 mA precharge into the reversed cell until its PCM cuts | not blocked (round1 m2, accepted; check polarity first, VERIFY E1) |

* USB input: J1 → **F1 PTC** (Bourns MF-MSMF110/16X, 1.1 A hold / 2.2 A trip, 16 V, 0.06–0.20 Ω) → D1 TVS SMF5.0A
  → VBUS. F1 limits a short in the neck cable while on USB. The worst-case normal draw is about 0.5 A, against a
  hold current of about 0.8 A at 60 °C (round2 R2-E3; the 0.75 A part had too little margin when warm).
  **This is not over-voltage protection** (round2 R2-E4). A 6.4–7.5 V source sits below the TVS's conduction and
  trips nothing, which puts VSYS at 5.6–6.6 V, above the ATtiny's and the LED board's 6 V absolute maximum. A hard
  over-voltage fault destroys the TVS before or as the PTC trips. Accepted for a USB-C 5 V-only sink, with real OVP
  (e.g. a TPS2595-class eFuse) on the next-revision list.
* **Q4 LED-board switch** (DMG2305UX, gate Q4_G driven from PB2 through R13 10 k, with C8 100 nF gate–drain and R12
  100 k pull-up to VSYS): off in reset and in the empty-battery sleep, so a flat cell is not drained by the LED board.
  VLED = VSYS − I·R_DS(on) (≈ 10–20 mV at 180 mA). **Soft turn-on** (round2 R2-E1): R13 into C8 holds the Miller
  plateau, so VLED ramps at about 2.5 V/ms. Charging the LED board's MLCCs then takes about 25–36 mA peak (SPICE,
  `docs/verification/spice-report_main-v0.1_led-v0.2_rev3.md` §2; corrected 2026-11-08 from the earlier 15–25 mA estimate:
  the MLCCs start near their unbiased ~11 µF and fall to ~4.5 µF at 3.5 V, so the start of the ramp draws most), where the
  unslowed gate gave multi-amp peaks that sagged VSYS, the MCU's supply, below its BOD level. Bench check: VERIFY E13.
  The I²C pull-ups (R8/R9 3.3 k) sit on VLED, so an unpowered LED board is never back-fed through SDA/SCL.
* **J4 pin 1 is VREF** (VSYS through R11 1 k) for the programmer's level sense only: never power the board from a
  programmer (round1 M3).

* Charge current: I = 1000 V / R_PROG = 1000 / 3.9 kΩ = **256 mA** (MCP73831 DS Eq. 5-1) ≈ 0.21 C for 1200 mAh
  (≈ 5 h to full). Lowered from 417 mA in round 1 (M4, m4): it keeps USB draw ≤ 0.5 A with the lamp on in most modes,
  and the charger dissipation ≤ ~0.7 W next to the pouch.
  MCP73831-2ACI/OT: 4.20 V ±0.75 %, 10 % preconditioning below 66.5 % V_REG, 7.5 % termination (31 mA),
  recharge at 96.5 % (~4.05 V). Thermal regulation in the charger limits current if the SOT-23-5 gets hot
  (worst case, IREG +10 % and V_PTH 2.79 V: (5.25 − 2.79) V × 0.282 A ≈ 0.69 W at the start of fast charge). No NTC
  input: charge at room temperature (user note; v0.2 MCP73833 + NTC).
* Q1–Q4 DMG2305UX: R_DS(on) ≤ 52 mΩ @ −4.5 V, ≤ 100 mΩ @ −2.5 V. The LED path runs through four FETs (Q3, Q1, Q2,
  Q4), then J3 and 2 × 200 mm of 28 AWG: about 4 × 0.075 Ω + 0.15 Ω ≈ 0.45 Ω, so ~80 mV at 180 mA. V_GS max ±8 V
  (worst case here 5.0 V).
* Q2 soft start: R7 10 kΩ into C5 100 nF (gate–source) → τ ≈ 1 ms. Q2 now charges only the main board's ~8 µF; the
  LED board's ~6 µF comes later, through Q4's soft turn-on. Round 1 simulated 0.7–1.3 A peak for ~0.1 ms into 14–21 µF
  (C5 is G–S, so there is no Miller dv/dt control), which is inside the FET and connector ratings.
* Q1 gate pull-down R5 **10 kΩ** (was 100 k): after USB unplug VBUS decays with τ ≈ 70 ms, so the load spends < 0.1 s
  on Q1's body diode (round1 m1). Costs 0.5 mA from VBUS only while USB is present.
* Standby drain with the switch OFF (battery only): Q2 I_DSS ≤ 1 µA, D3 reverse leakage (silicon, 4 V) ≪ 1 µA,
  MCP73831 output reverse leakage ≤ 2 µA (I_DISCHARGE), R5 sees 0 V, R6 sees 0 V. **Total ≤ ~3 µA** plus the cell's own
  PCM (~3–6 µA typical): about 0.1 % of capacity per month.

## 2. LED drive (LED board v0.2, 18 mm)

Design note for the redesign: `docs/design/led-board-v0.2.md`. Datasheet extract: `docs/datasheets/KEYSPECS.md`
(LP5012, SLVSEH2B).

* **TI LP5012** (WQFN-20, 3 × 3 mm), 12 constant-current sinks, all LED anodes on VLED. I_OUT = K_IREF × V_IREF /
  R_IREF = 105 × 0.7 V / 2.94 kΩ = **25.0 mA** per channel (Max_Current_Option 0: I_MAX 25.5 mA, ±5 %). Würth RGB
  abs max 30 mA. 11 channels used (8 white, R, G, B), one spare. ADDR1 = ADDR0 = GND → I²C **0x14**.
* PWM: 29 kHz, 12 bit (9-bit + 3-bit dithering), duty = OUTx_COLOR/255 × LEDx_BRIGHTNESS/255 (linear scale, set in
  DEVICE_CONFIG1 = 0x1C). Each LEDx_BRIGHTNESS covers three outputs, and on this board each bank mixes groups, so the
  firmware writes one brightness to all four banks and a colour per group. `lp_brightness()` picks the smallest
  brightness that still shows the strongest group (colours keep 7–8 bits for the mix ratios) with hysteresis, and
  writes are ordered so the in-between state is never brighter than either end (host-tested in `lib/core`). Level 0
  (0.4 % of full) is brightness 2 × colour 130: the minor channels of mixed modes quantise only near the bottom.
* Headroom: V_LED − V_f ≥ V_SAT (0.25 V typ, 0.35 V max at 20 mA; unspecified at 25 mA, likely ~0.3–0.45 V) for
  full current. White (~2.75 V, max ~2.92 V at 25 mA) and red (~2.1 V): regulated down to the 3.45 V low-battery
  threshold. **Green/blue (Würth, 3.2–3.6 V at 20 mA, ~+0.09 V at 25 mA)**: a typical die is regulated above
  V_LED ≈ 3.65 V; a maximum-V_F die needs ~4.05–4.15 V, above VLED on USB and on a full cell after the path drop, so
  it is never fully regulated (round3 R3-E3). The LP5012 has no per-channel current step (the TLC59116 design ran G/B at a 12.5 mA step),
  and PWM cannot lower the 25 mA peak, so the Green and Blue modes now run at full duty: below ~3.7 V of battery
  (typical dies) they dim gracefully, and the small G/B share of the mixed whites drifts slightly warm/magenta in
  the last ~30 % of the battery, or over most of it with a high-V_F die. Accepted; measure the received dies' V_F
  first (VERIFY E9). Remedy if they sit high: RIREF 3.65 kΩ (20 mA for every channel, −20 % white) or a known V_F bin.
* Würth RGB derating (datasheet p4): 30 mA flat to 50 °C ambient, then linear to 10 mA at 85 °C (25.0 mA at 58.8 °C,
  24.3 mA at 60 °C). The firmware derating (×0.3 at 52 °C) keeps the average far inside it; only a hung MCU holding
  G or B at 100 % between 58 and 60 °C would exceed it by 3–8 % (a double fault).
* Supply current: 4 mA typ / 6 mA max with 10 mA per output (SLVSEH2B §7.5); §8.4 says NORMAL is 10 mA typical, so
  budget 4–10 mA while any LED is on (VERIFY E7). ≤ 10 µA in power-save (all outputs 0 for 30 ms) and standby; the
  TLC59116 drew up to 29 mA. That multiplies the night-light runtime (§3).
* **One RGB LED** at the board centre (v0.1 had two): colour and night modes are about half as bright (red night
  1.1 lm, candle 2.4 lm, 6500 K 30 lm instead of 40 lm, because blue now sets the limit there); the whites are
  unchanged (34–61 lm of LED flux).
* **Thermal protection, three layers** (round1 M-1, F1, F4):
  1. Firmware derating on the MCP9800 reading: 100 % ≤ 45 °C → 30 % at 52 °C → 5 % at 58 °C. Slew ~10 %/s.
  2. Current caps: 200 mA total while the sensor is *trusted* (answering, −20…100 °C, and changing within 5 min of
     the load exceeding 50 mA); otherwise 110 mA, and 30 % if it stops answering for 3 s. The largest mode draws
     177.5 mA, so in practice the 200 mA cap never binds and the 110 mA one does. Cap changes fade over 160 ms. The
     MCP9800 runs at 12 bit (0.0625 °C), so the "changing" test sees normal noise.
  3. Hardware thermostat: MCP9800A0 ALERT (open drain, comparator, active low, TSET 60 °C / THYST 52 °C, fault queue
     2, set at every init) pulls the LP5012's EN low: shutdown, all outputs off. Works with a hung MCU or a dead bus.
     When ALERT releases, the LP5012 restarts with its registers reset and stays dark until the firmware re-inits it
     (it reads Chip_EN every second). EN has a 2.4 kΩ pull-up (round2 R2-E5), an 0402 on the board's TOP face in the
     gap between D1 and D2 (no room left on the bottom). MCP9800 POR defaults (80/75 °C) are a looser backstop until
     the firmware programs it.
* Recovery: 2 s watchdog; every 1 s the firmware reads back DEVICE_CONFIG0/1 (Chip_EN = 0 or a changed CONFIG1 →
  re-init, which zeroes every output in standby before Chip_EN) and the 16 output registers (any difference → full
  rewrite: a corrupted I²C burst no longer persists; round3 R3-F1/F2). After 4 failed inits the
  firmware writes the LP5012 RESET register (17h = FFh), then power-cycles the LED board through Q4, unless the
  thermostat is what holds it off. During the off time it drives SDA/SCL low, so VLED bleeds through the 3.3 k
  pull-ups (200 ms off) to well below the LP5012's 2.0 V UVLO (round2 R2-E2).

## 3. Runtime estimates (1200 mAh, ~4.4 Wh usable to 3.3 V)

LED current comes straight from the cell (linear sinks); the electronics (MCU idle-sleeping between 1 ms ticks,
LP5012 4–10 mA, MCP9800 0.2 mA) add about 7–12 mA while the light is on.

| Use | Battery current (approx.) | Runtime |
|---|---|---|
| 4000 K at full (177.5 mA LEDs at 25.0 mA/ch; derating may trim it once warm) | ~185 mA | ~6.5 h |
| Soft white at level 10 (16 % of full: ~19 mA LEDs) | ~26 mA | ~45 h |
| Red night light, level 4 (~0.4 mA LED) | ~8–12 mA (electronics-dominated) | ~100–150 h (VERIFY E7) |
| Empty-battery sleep (LED board off via Q4, MCU power-down + PIT) | ≤ ~30 µA (VERIFY F4) | months before the PCM cut-off |
| Switched off | ≤ ~10 µA incl. cell PCM | years (self-discharge dominates) |

## 4. I2C

Main board pull-ups 3.3 kΩ to VLED (switched VSYS); bus = MCU + 200 mm cable + LP5012 (0x14) + MCP9800A0 (0x48);
100 kHz. On boot the firmware clocks SCL until SDA is free: a reset mid-transfer can leave a slave holding SDA (neither
LED-board part has a bus time-out), and the recovery costs nothing.
Rise time with C ≈ 60–100 pF: 0.85·R·C ≈ 0.2–0.3 µs (Standard mode limit 1 µs). LP5012 V_IH = 1.4 V (fixed);
MCP9800 V_IH = 0.7 × VDD. The MCU runs on VSYS, and the LED board and pull-ups on VLED ≈ VSYS − 20 mV, so the levels
match.
