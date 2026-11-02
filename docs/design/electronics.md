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
| Battery reversed | — | — | — | Vgs ≈ 0 → off, body diode reverse → blocks | 0 |

* Charge current: I = 1000 V / R_PROG = 1000 / 2.4 kΩ = **417 mA** (MCP73831 DS Eq. 5-1) ≈ 0.35 C for 1200 mAh.
  MCP73831-2ACI/OT: 4.20 V ±0.75 %, 10 % preconditioning below 66.5 % V_REG, 7.5 % termination (31 mA),
  recharge at 96.5 % (~4.05 V). Thermal regulation in the charger limits current if the SOT-23-5 gets hot
  (worst case (5.0 − 3.0) V × 0.417 A = 0.83 W at the start of fast charge).
* Q1/Q2/Q3 DMG2305UX: R_DS(on) ≤ 52 mΩ @ −4.5 V, ≤ 100 mΩ @ −2.5 V; worst series drop at 300 mA and 3.3 V:
  ~3 × 0.075 Ω × 0.3 A ≈ 70 mV. V_GS max ±8 V (worst case here 5.0 V).
* Q2 soft start: R7 10 kΩ into C5 100 nF (gate–source) → τ ≈ 1 ms; inrush into ~25 µF on VSYS ≈ C·dV/dt ≈ 0.1 A.
* Standby drain with the switch OFF (battery only): Q2 I_DSS ≤ 1 µA, D3 reverse leakage (silicon, 4 V) ≪ 1 µA,
  MCP73831 output reverse leakage ≤ 2 µA (I_DISCHARGE), R5 sees 0 V, R6 sees 0 V. **Total ≤ ~3 µA** plus the cell's own
  PCM (~3–6 µA typical): about 0.1 % of capacity per month.

## 2. LED drive (LED board)

* TLC59116: I_OUT = (1.26 V / R_EXT) × 15 × CG; CG = 0.992 after power-up → R_EXT 750 Ω gives **25.0 mA**/channel
  (TI DS Eq. 3–5). Output knee ≈ 0.6 V at 26 mA (DS: I_O specified at V_O = 0.6 V).
* Headroom: V_LED − V_f ≥ 0.6 V for full current. White (Bridgelux, ~2.75 V at 25 mA): regulated down to V_LED ≈ 3.35 V
  (the whole usable battery range). Red (Würth, ~2.1 V): always. **Blue/green (Würth, ~3.2–3.3 V at 25 mA): regulated
  only above V_LED ≈ 3.9 V** — on USB (4.15 V) and the top ~40 % of the battery; below that blue/green dim
  progressively. This affects the Green/Blue modes and slightly shifts 6500 K and 4000 K (they use a little G/B).
  Recorded as a known limitation (no boost converter: it would add heat inside the moon).
* Low-end dimming: 8-bit PWM at 97 kHz per channel × IREF current-gain steps (CG 0.083–0.992) → ~3000:1 range.
* Supply current of the TLC59116 is 25–37 mA (max) while on — it dominates the night-light budget.

## 3. Runtime estimates (1200 mAh, ~4.4 Wh usable to 3.3 V)

| Use | Battery current (approx.) | Runtime |
|---|---|---|
| 4000 K at full (200 mA LED cap + ~30 mA electronics) | ~230 mA | ~5 h |
| Soft white at level 10 (~25 % of full) | ~80 mA | ~14 h |
| Red night light, level 3 | ~35 mA (driver-dominated) | ~30 h |
| Switched off | ≤ ~10 µA incl. cell PCM | years (self-discharge dominates) |

## 4. I2C

Main board pull-ups 3.3 kΩ to VSYS; bus = MCU + 200 mm cable + TLC59116 (0x60) + LM75B (0x48); 100 kHz.
Rise time with C ≈ 60–100 pF: 0.85·R·C ≈ 0.2–0.3 µs (Standard mode limit 1 µs). TLC59116 V_IH = 0.7 × VCC — all
devices share VSYS, so levels match.
