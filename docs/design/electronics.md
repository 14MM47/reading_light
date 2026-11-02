# Electronics design notes and calculations

Source of truth: `hardware/main-board/design.py`, `hardware/led-board/design.py`, `hardware/parts.py`.
Datasheet extracts with page references: `docs/datasheets/KEYSPECS.md`. Review findings and their dispositions:
`docs/verification/`.

## 1. Power path (main board)

| State | Q1 load-share (G = VBUS) | D3 S1J | Q2 load switch | Q3 rev-batt | VSYS |
|---|---|---|---|---|---|
| Battery only, switch ON | Vgs = −VBAT → on | reverse-biased (nA) | on | on (Vgs = −VBAT) | VBAT − I·(Rq1+Rq2+Rq3) |
| Battery only, switch OFF | on | reverse (nA) | off | on | 0 (VSYS_RAW = VBAT, isolated by Q2) |
| USB + battery, ON | Vgs ≈ VBUS − VSYS_RAW ≈ +0.85 V → off | forward, VSYS ≈ 5.0 − 0.85 = 4.15 V | on | on | ≈ 4.15 V from USB; charger sees only the cell → terminates normally |
| USB, switch OFF | off | forward | off | on | 0; charger runs (red LED) |
| Battery reversed, no USB | — | — | — | Vgs ≈ 0 → off, body diode reverse → blocks | 0 |
| Battery reversed + USB | — | — | — | charger biases Q3 on: ~42 mA precharge into the reversed cell until its PCM cuts | not blocked (round1 m2, accepted; check polarity first, VERIFY E1) |

* USB input: J1 → **F1 PTC** (Bourns MF-MSMF075-2, 0.75 A hold / 1.5 A trip) → D1 TVS SMF5.0A → VBUS. A sustained
  over-voltage makes the TVS conduct and trips the PTC; the PTC also limits a short in the neck cable while on USB.
* **Q4 LED-board switch** (DMG2305UX, gate = LED_EN_N on PB2, R12 100 k pull-up to VSYS): off in reset and in the
  empty-battery sleep, so a flat cell is not drained by the TLC59116. VLED = VSYS − I·R_DS(on) (≈ 10 mV at 200 mA).
  The I²C pull-ups (R8/R9 3.3 k) sit on VLED, so an unpowered LED board is never back-fed through SDA/SCL.
* **J4 pin 1 is VREF** (VSYS through R11 1 k) for the programmer's level sense only: never power the board from a
  programmer (round1 M3).

* Charge current: I = 1000 V / R_PROG = 1000 / 3.9 kΩ = **256 mA** (MCP73831 DS Eq. 5-1) ≈ 0.21 C for 1200 mAh
  (≈ 5 h to full). Lowered from 417 mA in round 1 (M4, m4): it keeps USB draw ≤ 0.5 A with the lamp on in most modes,
  and the charger dissipation ≤ ~0.5 W next to the pouch.
  MCP73831-2ACI/OT: 4.20 V ±0.75 %, 10 % preconditioning below 66.5 % V_REG, 7.5 % termination (31 mA),
  recharge at 96.5 % (~4.05 V). Thermal regulation in the charger limits current if the SOT-23-5 gets hot
  (worst case (5.25 − 3.0) V × 0.256 A ≈ 0.58 W at the start of fast charge). No NTC input: charge at room
  temperature (user note; v0.2 MCP73833 + NTC).
* Q1/Q2/Q3 DMG2305UX: R_DS(on) ≤ 52 mΩ @ −4.5 V, ≤ 100 mΩ @ −2.5 V; worst series drop at 300 mA and 3.3 V:
  ~3 × 0.075 Ω × 0.3 A ≈ 70 mV. V_GS max ±8 V (worst case here 5.0 V).
* Q2 soft start: R7 10 kΩ into C5 100 nF (gate–source) → τ ≈ 1 ms. The electrical review simulated 0.7–1.3 A peak
  for ~0.1 ms into ~14–21 µF (C5 is G–S, so there is no Miller dv/dt control): inside the FET and connector ratings.
* Q1 gate pull-down R5 **10 kΩ** (was 100 k): after USB unplug VBUS decays with τ ≈ 70 ms, so the load spends < 0.1 s
  on Q1's body diode (round1 m1). Costs 0.5 mA from VBUS only while USB is present.
* Standby drain with the switch OFF (battery only): Q2 I_DSS ≤ 1 µA, D3 reverse leakage (silicon, 4 V) ≪ 1 µA,
  MCP73831 output reverse leakage ≤ 2 µA (I_DISCHARGE), R5 sees 0 V, R6 sees 0 V. **Total ≤ ~3 µA** plus the cell's own
  PCM (~3–6 µA typical): about 0.1 % of capacity per month.

## 2. LED drive (LED board)

* TLC59116: I_OUT = (1.26 V / R_EXT) × 15 × CG; CG = 0.992 after power-up → R_EXT 750 Ω gives **25.0 mA**/channel
  (TI DS Eq. 3–5). Output knee ≈ 0.6 V at 26 mA (DS: I_O specified at V_O = 0.6 V).
* Headroom: V_LED − V_f ≥ knee (≈ 0.35–0.6 V) for full current. White (Bridgelux, ~2.75 V at 25 mA): regulated down
  to V_LED ≈ 3.35 V (the whole usable battery range). Red (Würth, ~2.1 V): always. **Green/blue (Würth, 3.2–3.6 V at
  20–25 mA)**: at 25 mA they regulate only above V_LED ≈ 3.7–3.9 V. Therefore the **Green and Blue modes run at half
  current** (12.4 mA, IREF step 0xBF): lower VF and knee, regulated down to about 3.6 V of battery (round1 M1). The
  mixed whites (3000/4000/6500 K, candle) use only a little G/B at up to 25 mA; their tint drifts slightly warm/
  magenta in the last ~30 % of the battery. Accepted for v0.1 (a boost converter would add heat in the moon; v0.2
  option: 5 V boost for the RGB anodes only). Bench check: VERIFY E9.
* Low-end dimming: 8-bit PWM at 97 kHz per channel × IREF current-gain steps 0.33 / 0.50 / 0.99 (8.3 / 12.4 / 24.8 mA,
  all inside the datasheet's 5–120 mA output ranges) → ~750:1 range. Below ~2 % the minor channels of mixed modes
  quantise (soft orange becomes red-orange at its lowest levels: accepted, round1 F9).
* Supply current of the TLC59116 is 25–37 mA (max) while on, and it dominates the night-light budget (VERIFY E7).
* **Thermal protection, three layers** (round1 M-1, F1, F4):
  1. Firmware derating on the LM75B reading: 100 % ≤ 45 °C → 30 % at 52 °C → 5 % at 58 °C. Slew ~10 %/s.
  2. Current caps: 200 mA total only while the sensor is *trusted* (answering, −20…100 °C, and changing within 5 min
     when > 50 mA flows); otherwise 110 mA, and 30 % if it stops answering for 3 s.
  3. Hardware thermostat: LM75B OS (comparator, active low, Tos 60 °C / Thyst 52 °C, set at every init) holds the
     TLC59116 RESET low. Works with a hung MCU or a dead bus. LM75B POR defaults (80/75 °C) are a looser backstop
     until the firmware programs it.
* Recovery: 2 s watchdog; MODE1 read-back every 1 s (a POR'd TLC re-initialises); after 4 failed inits the firmware
  power-cycles the LED board through Q4 (unless the thermostat is what holds it off).

## 3. Runtime estimates (1200 mAh, ~4.4 Wh usable to 3.3 V)

| Use | Battery current (approx.) | Runtime |
|---|---|---|
| 4000 K at full (182 mA LEDs at 25.0 mA/ch + ~30 mA electronics; derating may trim it once warm) | ~210 mA | ~5.5 h |
| Soft white at level 10 (~25 % of full) | ~70 mA | ~16 h |
| Red night light, level 4 | ~30 mA (driver-dominated) | ~40 h |
| Empty-battery sleep (LED board off via Q4, MCU power-down + PIT) | ≤ ~30 µA (VERIFY F4) | months before the PCM cut-off |
| Switched off | ≤ ~10 µA incl. cell PCM | years (self-discharge dominates) |

## 4. I2C

Main board pull-ups 3.3 kΩ to VLED (switched VSYS); bus = MCU + 200 mm cable + TLC59116 (0x60) + LM75B (0x48); 100 kHz.
On boot the firmware clocks SCL until SDA is free (a reset mid-transfer can leave a slave holding SDA; the TLC59116 has
no bus time-out).
Rise time with C ≈ 60–100 pF: 0.85·R·C ≈ 0.2–0.3 µs (Standard mode limit 1 µs). TLC59116 V_IH = 0.7 × VCC — all
devices share VSYS, so levels match.
