# Thermal and optical review: moon lamp head (LED board + PLA moon + PETG cup)

Reviewer: thermal/optics specialist. Date: 2026-11-02. I changed no repo files.
Scripts that produce every number below (re-runnable with `python3`):
`/tmp/claude-0/-home-user/7ba8e87c-d4ee-5a66-9891-51bde4e0a9a7/scratchpad/review/calc/` contains `budget.py`, `thermal.py`,
`run_cases.py`, `loop.py`, `tune.py`, `options.py`, `optics.py`, `intensity.py` and `modes_flux.py`.

Inputs read: `firmware/tools/gen_modes.py`, `include/modes_table.h`, `config.h`, `board_map.h`, `lib/core/lightcore.*`,
`src/main.cpp`, `docs/design/optics/sphere_illum.py` (+ .txt/.csv), `cad/parts/_lib/moonlib.py`, `cad/parts/moon_shell.py`,
`cad/parts/moon_base.py` (cup, found in the repo), `hardware/led-board/design.py`, scratchpad build diagnostics
(`out/moon_shell`, `out/moon_base`), KEYSPECS.md, and the Bridgelux DS312, Würth 150141M173100 and TLC59116 datasheets.
I read curves off the datasheet figures (pages rendered at 150–200 dpi).

---

## 0. Verdict

| # | Severity | Finding (short) |
|---|---|---|
| F1 | **BLOCKER** | The derating as specified (50/65/75 °C) settles the **PLA skirt that clamps the board at 50–52 °C, or 54 °C in a 30 °C room**. If derating does not act (for example a stuck sensor reading), it reaches 56 °C (49–64 °C). That is inside PLA's softening and creep band, at the part that carries the bayonet preload. |
| F2 | MAJOR | The "~0.6 W" thermal budget leaves out the TLC59116. Its linear sinks take 0.29–0.30 W and its quiescent current 0.06–0.12 W. At the 200 mA cap the head takes 0.90 W and keeps 0.75 W as heat. |
| F3 | MAJOR | Firmware `I_CHANNEL_MA 30.2` (REXT 620 Ω) does not match the hardware REXT of 750 Ω (25.0 mA). The 200 mA cap is really 166 mA. Correcting the constant on its own raises power: 4000K full goes from 166 to 182 mA. |
| F4 | MAJOR | There is no sensor-independent limit. The 30 % fail-safe covers only an I²C NACK. A stuck or implausible reading (SDA stuck low reads 0x0000 = 0 °C) or a thermally detached sensor still allows 200 mA. |
| F5 | MAJOR | The PLA skirt is the board clamp: the hottest PLA, 4–7 K below the board, under the 0.35 mm cam preload. Decoupling it from the board takes 8 K off the PLA peak. |
| F6 | MAJOR | "Reading light": 4000K full gives **22–31 lux at 25–30 cm** (range 16–40), and 13–19 lux after derating. Reading guidance is 300–500 lux, bedside reading ≥ 100–150. The thermal budget cannot close that gap. |
| F7 | MAJOR | The mode recipes use Kingbright 5050 RGB data, but the board has the Würth 150141M173100. Red is about 4× weaker. Night red gives 2.1 lm, not 9. Committed CANDLE renders yellow-green at xy (0.434, 0.483). NIGHT_ORANGE becomes 56 % 2700K. |
| F8 | MINOR | `sphere_illum.py` did not model the as-built geometry. It also has a small integrating-sphere error, an unused τ, and an azimuthal-mean metric. Re-run results: whites ≤ 1.04 ✓; single-CCT 2-D ≤ 1.14; RGB-only 1.06–1.14 ✗ (≤ 1.05 claimed). None of this is visible against the 3–6× lithophane contrast. |
| F9 | MINOR | Night-level colour resolution. The CG 0.083 step gives 2.1 mA peak, below the TLC's 5 mA minimum. Minor channels sit at 0–2 PWM counts at the default night levels. |
| F10 | MINOR | G/B regulate only at VLED ≥ ~3.65–3.7 V. On battery below that, the G/B correction in 3000/4000/6500K and candle fades and the colour shifts. |
| F11 | NOTE | Flicker: 97.6 kHz individual PWM is in IEEE 1789's no-observable-effect region at 100 % modulation. Compliant, as long as GRPPWM (190 Hz) stays unused. |
| F12 | NOTE | LED Tj ≤ 80 °C and TLC Tj ≤ 91 °C (worst case, no derating) against 125 and 150 °C. PETG cup ≤ 55–61 °C. Lithophane dome ~30 °C. Big margins everywhere except the PLA clamp. |

Bottom line: no hardware change is required to make the head safe. Firmware alone fixes F1, F3 and F4: correct the constant, use a 45/52/58 °C curve, and add a 110 mA sensor-independent cap plus a plausibility check. A cheap CAD change (F5: PETG clamp ring plus a gap pad) gets back about 50 mA of continuous output. A 10 kΩ resistor plus one trace (LM75B OS → TLC /RESET) adds a firmware-independent backstop.

---

## 1. Data and assumptions

| Quantity | Value used | Source / basis |
|---|---|---|
| White VF at 25 mA, Tsp 25 °C | 2.745 V; hot (ΔTj ≈ 35 K) 2.71 V | Bridgelux Fig. 9 (read at 25 mA); ΔVF/ΔT −1.04 mV/K (Table 4) |
| White flux at 25 mA | 17.3 % of the 150 mA flux: 2700K 8.8 lm, 5000K 9.7 lm | Fig. 10 (≈0.70 %/mA slope; 6.5 % at 10 mA, 35 % at 50 mA); Table 1, 51 / 56 lm typ |
| Flux vs Tsp | 0.955 at 55 °C, 0.925 at 70 °C | Fig. 11 |
| White efficacy at 25 mA | 128 lm/W (2700K), 141 lm/W (5000K), cold | 8.8 lm / (25 mA × 2.745 V) |
| LER of CRI-97 phosphor white | 285 lm/W ± 7 % (**ASSUMED**) | Typical of CRI ≥ 95 phosphor spectra |
| White radiant efficiency (WPE) | 45–50 % cold, **0.43 used** (hot, conservative: more heat) | 128–141 / 285, × 0.955 |
| Rj-sp (2835) | 31 K/W, defined on electrical power | Table 4 |
| Würth RGB at 25 mA | VF R 2.11 / G 3.35 / B 3.22 V; Iv 340 / 915 / 225 mcd → Φ = πIv = **1.07 / 2.87 / 0.71 lm** | Würth p3 VF–IF curve, p4 Iv–IF curve; 120° ≈ Lambertian |
| Würth RGB WPE | R ≈ 10 %, G ≈ 8 %, B ≈ 13 % | LER ≈ 200 / 450 / 68 lm/W (625 / 520 / 470 nm dominant) |
| Würth derating | IF max 30 mA to 50 °C ambient, linear to 10 mA at 85 °C | Würth p4 derating curve |
| TLC59116 | IOUT = 1.26 V/750 Ω × 15 × 0.992 = **25.0 mA**; knee 0.3 V at 5–20 mA, 0.45 V at 40 mA; ψJB 35.5 K/W; TSD ≥ 150 °C | Datasheet §7.4, Fig. 2, §9.5.9; design.py R1 = 750 Ω |
| TLC59116 ICC | **typ 15 mA (ASSUMED, not specified)**, max 29 mA (5.5 V, Rext 720 Ω) | Datasheet table: only a max is given. VERIFY on the bench (T0) |
| Geometry | Moon R_out 25, inner 22.4 (collar) → ~23.25 (relief mean), opening r 12.3 (33.3°), cut z −19.34; LED plane 1.8 mm below the cut; skirt r 12.0–16.7 × 2.5 mm; board Ø26 × 1.0 mm, clamp band r 12–13 (no Cu); cup OD 38.7 × 10.7 mm PETG, ledge under the board band, 2.2 mm cavity above an M10 nut | moonlib.py, moon_base.py, design.py (RING_R 8.0, RGB at x = ±3 mm) |
| Masses | Shell 12.9 cm³ PLA → 16 g, ≈ 20 J/K; cup 7.9 cm³ PETG → 10 g + steel nut, ≈ 14 J/K; board ≈ 1.6 J/K | Scratchpad diagnostics `volume_mm3`; c_p PLA 1.3, PETG 1.2, FR4 1.15 J/gK |
| Material limits | PLA Tg ≈ 55–60 °C, HDT(0.45 MPa) ≈ 55 °C, creep under load from ≈ 45–50 °C; PETG Tg ≈ 75–80 °C, HDT ≈ 68–70 °C | [memory] |
| PLA optics | ρ / τ / a = **0.70 / 0.20 / 0.10** central; range 0.55/0.35/0.10 (repo model) to 0.65/0.20/0.15 | ASSUMED. Kubelka–Munk with S ≈ 2/mm gives T(1.75 mm) ≈ 0.22, R ≈ 0.75. The repo's τ = 0.35 suits a ~1 mm wall, not the 1.76 mm mean |
| Ambient | 25 °C, still air (sensitivity at 30 °C) | brief |

---

## 2. Task 1: electrical, optical and heat budget

Definitions, per LED channel at average current I (PWM duty × 25 mA):
```
P_LED  = I·VF                    P_light = WPE·P_LED            P_LEDheat = P_LED − P_light
P_sink = I·(VLED − VF)           P_q     = VLED·I_CC            P_TLC     = P_sink + P_q
P_in   = VLED·(ΣI + I_CC)
```
Light fate (integrating sphere, §5.1): escapes 0.64, absorbed in the PLA wall 0.31, absorbed on the board 0.05.
- **Heat kept in the head** = P_in − 0.64·P_light.
- **Board heat** = P_LEDheat + P_TLC + 0.05·P_light.

Worked example, 200 mA of whites at VLED 4.20 V:
- P_LED = 0.200 × 2.71 = 0.542 W. P_light = 0.43 × 0.542 = 0.233 W. LED heat = 0.309 W.
- P_sink = 0.200 × (4.20 − 2.71) = 0.298 W. P_q = 4.20 × 0.015 = 0.063 W. P_TLC = 0.361 W.
- P_in = 4.20 × 0.215 = 0.903 W. Light out = 0.149 W. **Heat = 0.754 W.** Board heat = 0.682 W; wall heat = 0.072 W.

| Operating point (no derating) | I mA | P_in W | P_LED | light | LED heat | TLC sink | TLC q | **board heat** | wall heat | light out | **head heat** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 4000K full, USB 4.15 V, firmware as-is (cap really 166 mA) | 165.5 | 0.749 | 0.456 | 0.181 | 0.276 | 0.231 | 0.062 | 0.578 | 0.056 | 0.116 | 0.634 |
| 4000K full, USB 4.15 V, firmware corrected | 182.1 | 0.818 | 0.502 | 0.199 | 0.303 | 0.254 | 0.062 | 0.629 | 0.062 | 0.127 | 0.691 |
| All whites full (= 200 mA cap), USB 4.15 V | 200 | 0.892 | 0.542 | 0.233 | 0.309 | 0.288 | 0.062 | 0.671 | 0.072 | 0.149 | 0.743 |
| All whites full, battery 4.20 V | 200 | 0.903 | 0.542 | 0.233 | 0.309 | 0.298 | 0.063 | **0.682** | 0.072 | 0.149 | **0.754** |
| All whites full, battery 3.70 V | 200 | 0.796 | 0.542 | 0.233 | 0.309 | 0.198 | 0.056 | 0.574 | 0.072 | 0.149 | 0.646 |
| Worst: 200 mA at 4.20 V, I_CC = 29 mA | 200 | 0.962 | 0.542 | 0.233 | 0.309 | 0.298 | 0.122 | 0.741 | 0.072 | 0.149 | 0.813 |
| Sensor-NACK fail-safe (30 % → 60 mA), 4.20 V | 60 | 0.315 | 0.163 | 0.070 | 0.093 | 0.089 | 0.063 | 0.249 | 0.022 | 0.045 | 0.270 |
| Night red at max level 11 (11.5 mA avg), 4.20 V | 11.5 | 0.111 | 0.024 | 0.002 | 0.021 | 0.025 | 0.063 | 0.109 | 0.001 | 0.002 | 0.110 |

Observations:
- At full output the driver's share of board heat is 0.36 / 0.68 = **53 %**. The linear sink burns 1.4–1.5 V per white channel at 4.15–4.2 V. That is more than half of each LED's own VF.
- In night modes the TLC's quiescent current dominates: 63 mW of 110 mW. This also matters for battery life; that belongs to the electrical review.

---

## 3. Task 2: steady-state temperatures and time constants

### 3.1 Network (7 nodes; `thermal.py`)

Nodes:
- B: board, lumped; local rises added afterwards.
- Sc: PLA skirt surface at the clamp band.
- Ai: air inside the moon.
- Wi / Wo: lithophane shell inner and outer surface.
- Ci: PETG cup around the ledge, floor and nut.
- Co: PETG cup outer surface.

Each path is listed with its nominal value, then optimistic / pessimistic:

| Path | Derivation | R (K/W) |
|---|---|---|
| Wo → ambient | Churchill sphere: Ra(D 50 mm, ΔT 5 K) ≈ 5×10⁴ → Nu ≈ 8.8 → h_c 4.7 W/m²K; h_r = εσ(T₁²+T₂²)(T₁+T₂) ≈ 5.7 (ε 0.92). Sum 10.4 × 69.6 cm² (sphere above the rim + collar cone) | 14 |
| Wi → Wo | Conduction t/(kA) = 1.76 mm / (0.13 × 66 cm²) | 2 |
| B → Wi, radiation | ε 0.88, A_top 4.52 cm², view factor 0.81 through the opening (disk to coaxial disk at 2.5 mm, r 12) | 420 |
| B → Ai → Wi | Hot plate facing up, L = A/P = 6 mm: h ≈ 7.5–11 → 210 K/W; air → wall h 2.5 × 62 cm² → 65 K/W | 275 |
| B → Ci, bottom gap | Still air, 2.2 mm: k·A/g = 0.0275 × 4.52e-4/2.2e-3 = 5.6 mW/K; TLC top ~1 mm from the nut +1.2 mW/K; radiation ε_eff 0.56 +1.7 mW/K | 115 |
| B → Ci, edge (ledge + pocket wall) | In-plane Cu to r 12 (≈8) + 1 mm Cu-free FR4 band (≈8) + contact (h_c 1000 W/m²K × 78.5 mm² = 13) + 2-D spreading into PETG from a 1 mm band, ln(4H/w)/(πkL) ≈ 50; 0.2 mm pocket air gap in parallel | 50 (35 / 80) |
| B → Sc (to the PLA surface) | 8 + 8 + 13 | 29 (20 / 45) |
| Sc → Wi | Spreading from a 1 mm band into PLA (≈72), up 2.5 mm of skirt (≈45), then into a 2.6 mm shell that behaves as a poor fin: √(h·k·t)·2πr → ≈130 | 220 (150 / 320) |
| Sc → Ci | Lateral in PLA to the PETG step (≈120) + contact 3 + PETG ≈30 | 150 (100 / 220) |
| Ci → Co | 7 mm-thick PETG ring/floor: radial ln(19.35/12.6)/(2π·0.2·7.2 mm) = 47 in parallel with the floor | 30 (20 / 45) |
| Co → ambient | Side 13.0 cm² (h_c ≈ 8, short vertical cylinder) + bottom 10.9 cm² (h_c ≈ 3, 70 % radiation view) + rim 2.8 cm²; h_r ≈ 5.7 | 33 |
| Gooseneck | Neglected (brief); optimistic set adds 0.004 W/K | — |

Results:
- **Board → ambient is effectively 48 K/W (38–62)** per W of board heat.
- **The PLA clamp rises 46 K/W (37–58).**
- At 200 mA, about 0.30 W flows into the cup, about 0.14 W into the PLA skirt, and only about 0.16 W leaves the board top into the moon. A 26 mm board in a closed cavity cannot shed heat through its own faces, so the small PETG cup (27 cm² outside) becomes the main path.

Local rises:
- **White LED Tj** = T_B + 31 × 0.068 + 80 × 0.039 = T_B + 5.2 K. The cathode pad is an island in the VLED pour (R_island ≈ 80 K/W).
- **TLC Tj** = T_B + 8 × P_TLC/2 + ψJB 35.5 × P_TLC.
- **LM75B** reads T_B + ~1 K. It sits 3.5 mm from the TLC body. ASSUMED; calibrate on the bench.

### 3.2 Predicted steady-state temperatures (25 °C still air, **no derating**)

Format: nominal [optimistic – pessimistic], °C.

| Node | (a) 4000K full, 4.15 V, fw as-is 166 mA | (b) 4000K full, fw fixed 182 mA | (c) 200 mA, USB 4.15 V | (d) 200 mA, batt 4.20 V | (e) 200 mA, batt 3.70 V | (f) 200 mA, 4.2 V, I_CC 29 mA | (g) fail-safe 60 mA |
|---|---|---|---|---|---|---|---|
| White LED Tj (limit 125) | 61 [54–69] | 63 [56–73] | 66 [58–75] | 66 [58–76] | 61 [54–69] | 69 [61–79] | 41 [37–44] |
| TLC59116 Tj (TSD ≥ 150) | 67 [61–76] | 71 [64–80] | 74 [67–84] | 75 [67–85] | 66 [59–74] | 80 [72–91] | 45 [42–49] |
| Board mean | 55.7 [49–64] | 58.2 [51–67] | 60.3 [53–70] | 60.8 [53–71] | 55.6 [49–64] | 63.6 [55–74] | 38.9 [36–43] |
| LM75B reading | 56.7 | 59.2 | 61.3 | 61.8 | 56.6 | 64.6 | 39.9 |
| **PLA skirt at the clamp** (soft ≈ 55–60) | **51.7 [46–59]** | **53.9 [48–61]** | **55.7 [49–64]** | **56.2 [50–64]** | **51.7 [46–59]** | **58.6 [52–67]** | 37.1 [35–40] |
| Air inside the moon | 35.9 [33–39] | 36.9 [34–41] | 37.8 [35–42] | 38.0 [35–42] | 36.0 [33–40] | 39.1 [36–44] | 29.6 |
| Lithophane shell (lumped) | 29.3 | 29.7 | 30.0 | 30.1 | 29.5 | 30.4 | 26.9 |
| PETG cup at the ledge (Tg ≈ 75–80) | 45.7 [42–51] | 47.4 [43–53] | 48.8 [44–54] | 49.2 [44–55] | 45.7 [42–51] | 51.0 [46–57] | 34.5 |
| PETG cup outside | 36.0 | 36.8 | 37.5 | 37.6 | 35.9 | 38.5 | 30.2 |

Notes on the table:
- **Room at 30 °C, case (d), nominal:** board 65.5, PLA clamp 60.9, LED Tj 70.7, TLC Tj 79.7.
- **Lithophane shell:** this is the lumped area average. The collar band next to the skirt runs between the shell and clamp values, roughly 35–45 °C. The dome stays near ambient + 5 K, so the lithophane itself is not at risk. Only the skirt, lugs and clamp band are.
- **Comparison with the limits:** LEDs have ≥ 45 K margin, the TLC ≥ 59 K and PETG ≥ 20 K. **The PLA clamp has no margin:** 50–64 °C in every full-output case.

### 3.3 Time constants: how long full brightness lasts

`loop.py` integrates the network with implicit Euler. It reads the LM75B at 1 Hz and slews 10 %/s, exactly as `lightcore.cpp` does.

Without derating, 200 mA at 4.15 V, from a 25 °C start:

| | opt | nom | pes |
|---|---|---|---|
| Board t63 / t95 | 4.2 / 18 min | **4.9 / 22 min** | 5.4 / 25 min |
| Board at 1 / 2 / 5 / 10 / 20 min | 35 / 39 / 44 / 48 / 52 | 37 / 41 / 47 / 53 / 58 | 39 / 45 / 53 / 59 / 66 |
| LM75B reaches 50 °C (current curve starts derating) | 11.4 min | **6.2 min** | 3.3 min |
| PLA clamp reaches 50 °C / 55 °C | — / — | 11.7 / 29 min | 7.2 / 11.8 min |

The board has a fast pole of about 20–40 s (1.6 J/K against ~14 K/W, the parallel sum of its local paths). The slow pole of 5–6 min comes from the PETG cup and the shell (~35 J/K against ~10 K/W). After switch-off, the board cools 63 % in 5.4 min.

**So full brightness lasts about 6 min (3–11 min) before the current curve starts derating, and about 3 min (2–5 min) with the curve proposed below.** The derating loop is stable: its gain is about 1.7 against a 5 min plant time constant with a 1 s sample. No limit cycling appears in the simulation.

---

## 4. Task 3: derating curve, hard cap, REXT

### 4.1 Where the current curve settles

Closed-loop equilibrium with 200 mA requested (whites), VLED 4.2 V:

| Curve (full ≤ / 30 % at / 5 % ≥, °C on the LM75B) | nom 25 °C: kept mA, sensor, **PLA** | pes 25 °C | pes 30 °C room |
|---|---|---|---|
| **Current: 50 / 65 / 75** | 154 mA, 54.9, **50.2** | 128 mA, 57.7, **52.2** | 113 mA, 59.3, **54.3** |
| 45 / 55 / 60 | 125 mA, 50.3, 46.2 | 100, 52.1, 47.4 | 83, 53.3, 49.2 |
| **Proposed: 45 / 52 / 58** | **117 mA, 49.1, 45.1** | 92, 50.4, 46.0 | 73, 51.3, 47.5 |
| 42 / 50 / 56 | 106, 47.4, 43.6 | 83, 48.7, 44.5 | 65, 49.7, 46.1 |
| 40 / 48 / 55 | 97, 45.9, 42.3 | 76, 47.1, 43.1 | 58, 48.2, 44.8 |

**The current curve is wrong for this mechanical design.**
- The LED (125 °C) and TLC (150 °C) limits are never in play.
- The only constraint is the PLA clamp. It sits 4–7 K below the sensor at full power and 1–3 K below at low power.
- A curve that starts at 50 °C parks the PLA at 50–54 °C indefinitely, under preload.
- The 65 and 75 °C points protect nothing that matters here, except PETG at the extreme.

**Recommendation: full ≤ 45 °C, linear to 30 % at 52 °C, 5 % at ≥ 58 °C** (sensor reading).
- Keep the 10 %/s slew and the 30 % NACK fail-safe.
- Expected behaviour at 4000K full (nominal): full output for about 3 min, then a slow fade to about 60 % over 20 min. 182 mA becomes about 117 mA, roughly −0.7 stop.
- The PLA clamp then sits at ≤ 45 °C nominal and ≤ 47.5 °C (pessimistic, 30 °C room).
- The slow fade (< 0.1 %/s) is invisible.
- If Matt rejects the fade, the alternative is to lower the 4000K and 6500K maximum level so their full drive is ≤ 120 mA.

### 4.2 Sensor-independent hard cap

Steady state with no derating at all, which models a stuck-low or detached sensor:

| Total white mA at 4.2 V | Board heat W | PLA clamp nom 25 °C | pes 25 °C | pes 30 °C |
|---|---|---|---|---|
| 100 | 0.372 | 42.7 | 47.4 | 52.1 |
| **110** | 0.403 | **44.1** | **49.1** | 53.9 |
| 120 | 0.434 | 45.5 | 50.8 | 55.6 |
| 140 | 0.496 | 48.2 | 54.2 | 59.0 |
| 160 | 0.558 | 50.9 | 57.6 | 62.3 |
| 200 | 0.682 | 56.2 | 64.3 | 68.9 |

**Recommended hard cap: limit board heat to 0.40 W.**
```
I_max = (0.40 W − VLED·I_CC) / (VLED − 1.1 V)        (1.1 V ≈ WPE·VF of the light that leaves the board)
      = 109 mA @ 4.20 V, 111 mA @ 4.15 V, 132 mA @ 3.70 V   → use 110 mA for VLED ≥ 3.9 V, 130 mA below
```
- Apply it whenever the sensor is not *valid and plausible*.
- Allow up to 200 mA, still governed by the 45/52/58 curve, only while it is.

Plausibility, which costs about 30 lines of firmware:
- Reject readings below −20 °C or above 110 °C.
- Reject raw 0x0000 or 0xFFFF repeated three times (SDA stuck low makes every address byte look ACKed and reads 0 °C).
- Reject a reading that stays identical to the LSB for more than 60 s while drive power changes by more than 50 %.
- Expect a rise of at least 3 K within 10 min of any step to ≥ 150 mA.
- Any failure latches the hard cap until power-cycle.
- Optional second layer: a first-order firmware estimate (τ = 300 s, 52 K/W × board heat computed from drive and VLED) used as max(T_sensor, T_model).

If the bench test (§7, T2) measures a pessimistic R (PLA rise > 55 K/W per W of board heat), use 90 mA.

**Hardware backstop (LED board v0.1, one trace and one resistor):**
- Today TLC59116 /RESET (pin 25) is tied to VLED. Instead, drive it from LM75B OS (pin 3, open-drain, active-low by default) with a 10 kΩ pull-up to VLED.
- The firmware programs Tos 60 °C, Thyst 52 °C and fault queue 2 at boot.
- If the firmware never programs it, the power-on defaults (80/75 °C) still cut the LEDs.
- After an OS reset the TLC comes up with its oscillator off, so the LEDs stay dark. This fails safe. Add a periodic MODE1 read-back and re-init in `main.cpp`.

### 4.3 Lower REXT to 20 mA?

**No, not for thermal reasons. Keep 750 Ω (25 mA).**
- Heat per lumen is the same. At 20 mA, flux is 13.8 % of the 150 mA flux against 17.3 % at 25 mA (ratio 0.80). Electrical power ratio is 20 × 2.72 / (25 × 2.745) = 0.79.
- Head heat is set by the *total* current cap and VLED, not by per-channel current.
- 20 mA would cut the single-group modes (WARM_2700, WHITE_5000; ≤ 114 mA, already under the cap) by 20 % for no benefit.
- As a backstop it is weak: all 14 channels at 20 mA is still 280 mA, which is not PLA-safe.
- Consider 910 Ω (20.6 mA) only if the bench shows G/B dropout on battery (F10: the G VF falls from 3.35 to 3.22 V, so regulation holds to about 3.55 V) or Würth derating problems.

### 4.4 Mechanical changes that buy back output (`options.py`)

At 200 mA and 4.2 V (nominal / pessimistic):

| Change | Board | PLA peak | Cup |
|---|---|---|---|
| Baseline | 60.8 / 70.7 | 56.2 / 64.3 | 49.2 / 54.8 |
| PETG clamp ring holds the board; PLA skirt seats only on the PETG step with a ≥ 0.5 mm air gap to the board | 62.6 / 72.2 | **48.3 / 55.7** | 50.3 / 56.0 |
| 2.0–2.5 mm silicone gap pad (≥ 3 W/mK) filling the cavity: GND pour → cup floor / M10 nut (cut-outs for TLC/LM75B/pads) | 53.5 / 60.7 | 51.1 / 57.4 | 52.8 / 60.0 |
| **Both** | 54.3 / 61.4 | **46.9 / 53.1** | 53.5 / 60.6 |

With both changes, the sensor-independent cap can rise to **160 mA**: PLA 43.2 °C nominal, 48.3 °C pessimistic, cup ≤ 55 °C.
- The decoupling also removes the creep-under-preload mode. Today CAM_DROP 0.35 mm "pulls the moon down onto the LED board", so the hottest PLA carries a permanent compressive load and the lugs carry its reaction. Above about 45 °C the preload relaxes and the moon can loosen.
- Venting (a pole hole plus cup slots) gives about 0.05 W of chimney flow at ΔT 15 K. Not worth the look.

---

## 5. Task 4: optics

### 5.1 `sphere_illum.py`: maths check

| Item | Status |
|---|---|
| Direct term `I0·cos a·cos b/d²`, inward normal, per-LED normalisation, ring-area weights, η = Φ_wall/(πI0) | Correct |
| Indirect term `ρΦ_wall/(A_wall(1−ρf_wall))` | Small error. The standard form is ρΦ/(A_total(1−ρ̄)) with ρ̄ including the port. The code divides by A_wall (+4–8 %), treats the port as black (−3–8 % when the white board has ρ ≈ 0.7), and drops the 3 % of flux that misses the wall. Net effect on uniformity < 0.5 %, on absolute level < 10 % |
| `TAU` | Declared, never used. The model has no absolute output and no escape efficiency |
| Geometry swept | Only R 23.6, openings 25/30°, a **centre LED + 8 on r 6.5**. As-built is R_in 22.4 → ~23.25, 33.3°, **8 whites on r 8.0 (WW/CW alternating, 4-fold per CCT), RGB at x = ±3 mm with emitters 1.9 mm tall, no centre LED**, plus the skirt bore. B4's "30–35°" was extrapolated from these runs |
| Metric | max/min of the *azimuthal mean* above φ_o + 10°. This hides azimuthal ripple from 4- and 2-LED groups |
| Physics | Sound. A Lambertian source *on* a sphere and aimed at its centre gives exactly uniform illuminance. With the LED plane 1.8 mm below the cut, the r = 8 LEDs sit 0.2 mm below the virtual sphere (z −21.14 vs −20.94), which is why it works. The 1.9 mm-tall RGB packages sit about 1 mm *above* it, which is why they are worse |

Reproduction: 30°, dz −1.8 gives 1.007, matching the CSV. Repo layout on as-built R gives 1.02.

As-built re-run (`optics.py`; corrected indirect term, ρ_port 0.7, skirt occlusion):

| LED group | Flux to wall | Meridional max/min θ > 43° | Full 2-D θ > 43° | 2-D θ > 50° | Comment |
|---|---|---|---|---|---|
| All 8 whites | 0.973 | 1.025 (1.017–1.037 for ρ 0.80–0.55) | 1.028 (1.02–1.04) | 1.011 | Claim holds |
| One CCT (4 LEDs) | 0.973 | 1.025 | **1.096 (1.07–1.14)** | 1.051 | 4-fold ripple in the collar band |
| RGB only (2 LEDs, ±3 mm, 1.9 mm tall) | ~1.0 | **1.090 (1.06–1.14)** | **1.124 (1.08–1.19)** | 1.096 | 2-fold pattern; bottom/top 0.92–0.96. **Fails ≤ 1.05** |
| All 10 | 0.981 | 1.009 | 1.021 | 1.011 | |

What the model ignores, in order of visual importance:
1. **Lithophane transmittance contrast.** The τ(0.9 mm)/τ(2.6 mm) ratio is about 3–6× (ASSUMED; Kubelka–Munk plus absorption). It dominates appearance by more than an order of magnitude over any of the above. An illumination gradient up to about 1.15–1.2 would not be noticed. The B4 tolerance can be relaxed to ≤ 1.15, and the "≤ 1.05" claim should be qualified to "all-white modes, azimuthal mean".
2. **The collar band.** At θ 33–50° the wall is held at 2.6 mm (darkest), and the cup rim hides θ ≲ 45° from side views. Expect a dark lower rim, which is not an illumination effect.
3. **Relief radius ±0.85 mm and relief slopes.** These give about ±4–7 % local E, again inside the image.
4. **Off-centre RGB and alternating WW/CW.** In 4000K, the local WW:CW mix at the collar varies about ±7 %, so Δx ≈ ±0.004. That is 1–2 MacAdam steps and only at the lowest band.
5. **Board self-shadowing.** The 1.9 mm RGB bodies block about 2 % of each white LED's grazing flux, in ±12° azimuth wedges. The skirt bore intercepts 2.7 % of white flux and re-emits it diffusely. Both negligible.
6. **The cup wall.** It is outside the light path because the board closes the opening. Light through the PLA skirt into the cup is lost (< 2 %).

**Escape efficiency** (now that τ is used):
```
W = η/(1 − ρ(f_w + ρ_p·f_p)),   f_p = 475/6575 = 0.072,   escape = τ·W
```
- ρ/τ = 0.70/0.20: W = 0.973/0.315 = 3.08, **escape 0.62 + ~0.02 via the skirt ≈ 0.64** (wall absorbs 0.31).
- Repo values 0.55/0.35: escape 0.74.
- Lossier PLA 0.65/0.20/0.15: escape 0.54.

### 5.2 Flux and page illuminance

Moon intensity vs view angle (`intensity.py`): a uniform-luminance sphere with the collar at half luminance and the cup occluding.

| α from straight down | 0° | 30° | 45° | 60° | 90° | 180° |
|---|---|---|---|---|---|---|
| I / (Φ_out/4π) | 0.47 | 0.56 | 0.70 | 0.84 | 1.06 | 1.17 |

For a page below and in front of the lamp, use α 30–45° (factor 0.63; 0.56–0.70). Page illuminance:
```
E = 0.63·Φ_out/(4π·d²)     (normal incidence; ×0.87 for a 30° tilt)
```
Flux is emitted at 25 °C; out = × 0.955 (hot, whites) × 0.64.

| Mode / state | Emitted lm | Out of moon lm (range) | E at 25 cm | E at 30 cm | At the eye, 50 cm horizontal |
|---|---|---|---|---|---|
| 4000K full, firmware as-is (166 mA) | 58 | 36 | 28 lux | 20 lux | 12 lux |
| **4000K full, 182 mA (cold, first 3–6 min)** | 64 | **39 (33–45)** | **31 (24–40)** | **22 (16–28)** | 13 lux → 9 mel-EDI (DER 0.71) |
| 4000K, settled on the proposed curve (~117 mA) | 41 | 25 | 20 | 14 | 8 |
| 4000K under the 110 mA hard cap | 39 | 24 | 19 | 13 | 8 |
| All whites, 200 mA (cold) | 74 | 45 | 36 | 25 | 15 |
| WARM_2700 full (100 mA) | 35 | 21.5 | 17 | 12 | 7 |
| WARM_2700 default (level 9, 11 %) | 3.9 | 2.4 | 1.9 | 1.3 | 0.8 |

Mean moon luminance at 4000K full is I/(πR²) ≈ 3.3 cd / 1.96e-3 m² ≈ 1700 cd/m², and about 3–5 kcd/m² over the thin regions.

**Comparison:**
- Reading guidance is about 300–500 lux on the page (IES / EN 12464-1 [memory]). Bedside reading is commonly 100–300 lux.
- The moon gives 15–30 lux at 25–30 cm, 3–20× short. It is enough to find a page or read large print briefly, not a reading light.
- Closing the gap with the moon alone needs Φ_out ≈ 100 lux × 4π × 0.09 m² / 0.63 ≈ 180 lm, about 280 lm emitted and about 2.5–3 W in the head. With PLA ≤ 45 °C the head can shed about 0.4 W. **This is a physical limit of a diffuse 50 mm sphere.**
- The efficient fix is a directional downlight. A single 2835 at 25 mA aimed down gives 2.8 cd on axis, 31 lux at 30 cm, which equals the whole moon. Add a 30° optic and it gives about 30 cd, about 330 lux, for +0.08 W of board heat. The cup's centre is the M10 neck, so the LED would sit at r ≈ 10 mm firing through the cavity and floor. That is a design decision for Matt.
- At the eye, 4000K full gives about 9 mel-EDI, at the 10 lux evening limit. Keep it labelled as a day mode.

### 5.3 Night modes

Regenerated recipes with the real LEDs (`modes_flux.py`). Out of moon = 0.64 × emitted. Luminance = I_horizontal/(πR²).

| Mode | Full lm (real) [table claims] | Level (fraction) | Out lm | E at 30 cm | E at 1 m | Moon luminance |
|---|---|---|---|---|---|---|
| NIGHT_RED | 2.14 [9] | default 3 (1.21 %) | 0.017 | 0.009 lux | 0.0008 | 0.7 cd/m² |
| | | max 11 (22.9 %) | 0.31 | 0.17 lux | 0.016 | 13 cd/m² |
| | | (100 %) | 1.37 | 0.76 lux | 0.07 | 59 cd/m² |
| NIGHT_ORANGE (regenerated) | 3.1 [13] | default 4 (1.74 %) | 0.035 | 0.019 lux | 0.002 | 1.5 cd/m² |
| | | max 10 (15.9 %) | 0.31 | 0.17 lux | 0.016 | 13 cd/m² |
| CANDLE_1900 (regenerated) | 4.8 [20] | default 7 (5.3 %) | 0.16 | 0.09 lux | 0.008 | 7 cd/m² |
| | | max 13 (47.9 %) | 1.46 | 0.81 lux | 0.07 | 63 cd/m² |

**Comparison:**
- Night-light guidance is ≤ 1 lux mel-EDI for sleep and ≤ 10 lux if vision is needed (Brown 2022). Every night mode is ≤ 1 lux photopic at 30 cm, and red's mel DER is 0.003, so all comply with a wide margin.
- If anything, red is **too dim to be useful** at its maximum level 11 (0.17 lux at 30 cm). Raise NIGHT_RED max_level to 15 (0.76 lux at 30 cm, 0.07 lux at 1 m): still compliant.
- The defaults (0.7–7 cd/m² glow) are sensible as a "visible moon" in a dark room.

**F7 detail: the committed recipes on the real LEDs**
- CANDLE_1900 → xy (0.4335, 0.4829), luminance shares WW 23 % / R 23 % / **G 54 %**. That renders yellow-green, Duv ≈ +0.05.
- NIGHT_ORANGE → xy (0.582, 0.353), shares WW 56 % / R 44 %. Mel DER is about 0.26 against the 0.14 intended.
- COOL_6500 → xy (0.320, 0.336), about 0.012 off target.
- Regenerated with the Würth and Bridgelux data at 25 mA, the drive ratios are:
  - WHITE_3000: WW 1.000 / CW 0.152 / G 0.117
  - WHITE_4000: WW 0.639 / CW 1.000 / G 0.188
  - WHITE_5000: WW 0.064 / CW 1.000 / B 0.151
  - COOL_6500: CW 1.000 / G 0.216 / B 0.959
  - CANDLE_1900: WW 0.022 / R 1.000 / G 0.322
  - NIGHT_ORANGE: WW 0.026 / R 1.000
- The Würth G/B chromaticities in that solve are approximate (G (0.15, 0.72), B (0.13, 0.08)). Confirm them with a spectrometer.
- The "lm at full drive" comments in `modes_table.h` are emitted lumens at 30 mA with the wrong RGB part. **Delivered light is about 0.6× the emitted value.** For example, 4000K "89 lm" is really 64 lm emitted and 39 lm out.

**F9 detail: night-level resolution**
- At the lowest IREF code (CG 0.0833) each output sinks 25 × 0.0833/0.992 = **2.1 mA peak**. The TLC's recommended minimum is 5 mA, and below it current accuracy and matching are unspecified.
- NIGHT_ORANGE's WW component at level 4 works out to 0.026 × 0.0174 × 0.992/0.0833 × 255 ≈ 1.4 counts, so it quantizes to 1 (±35 %). Below level 3 it rounds to 0 and the mode becomes pure red.
- Accept this, or define per-level recipes that drop the minor channel cleanly. Avoid GRPPWM dimming (190 Hz, see F11).

**F10 detail:** G (3.35 V) and B (3.22 V) plus a ~0.3 V knee need VLED ≥ 3.65 V. Below about 3.7 V on battery, the G and B correction in 3000K, 4000K, 6500K and candle falls off and the whites drift by up to about 0.01 in xy.

### 5.4 Flicker (F11)

- The TLC59116 individual PWM runs at 25 MHz/256 = **97.6 kHz**.
- The firmware uses LDR = 10 (individual PWM only); GRPPWM/GRPFREQ are unused.
- IEEE 1789-2015 places no limit on modulation depth above 3 kHz (no observable effect) or above 1.25 kHz (low risk). **Compliant at 100 % modulation, at every level.** Stroboscopic visibility (SVM) is negligible above about 2 kHz.
- Keep it that way:
  - Never use GRPPWM/LDR = 11 for dimming. At 190 Hz, 100 % modulation is far above the low-risk 15 % (0.08 × 190) and the no-effect 6.3 %.
  - Never use GRPFREQ "blink" for effects.
- The save-confirmation and low-battery dips are single, intentional events, not periodic flicker.
- Cable and VLED ripple at 97.6 kHz affects light only for G/B when they are out of headroom (F10), and then still at 97.6 kHz.

---

## 6. Findings with severity (detail)

- **F1 BLOCKER: PLA clamp at its softening point.**
  - Evidence: §3.2 and §4.1. The current curve's equilibrium puts the PLA clamp at 50.2 / 52.2 / 54.3 °C (nominal / pessimistic / 30 °C room). With no derating it reaches 56 °C (49–64).
  - The skirt carries the bayonet preload (CAM_DROP 0.35 mm), so creep and loosening are the expected failures, not visible melting.
  - Fix in firmware only: the §4.1 curve plus the §4.2 cap and plausibility check.
- **F2 MAJOR: budget omits the driver.** 0.29–0.30 W of sink loss plus 0.06–0.12 W quiescent. The head takes 0.90 W at 200 mA, not 0.6 W. Update the `I_CAP_MA` comment and any design notes.
- **F3 MAJOR: stale `I_CHANNEL_MA 30.2`.** The hardware is 25.0 mA (750 Ω). Fix it to 25.0 *in the same change* as the new cap and curve. On its own, the fix raises 4000K full by 10 % (+2.5 K at the board).
- **F4 MAJOR: no protection against a wrong-but-answering sensor.** SDA stuck low reads 0 °C; a cracked LM75B joint or detached board reads too low. Fix with the §4.2 plausibility check, 110 mA cap and LM75B OS → /RESET.
- **F5 MAJOR: the hottest PLA is structural.** Clamp the board with PETG and keep PLA ≥ 0.5 mm away; add the gap pad. Together these cut the PLA peak by 9 K and allow a 160 mA continuous cap.
- **F6 MAJOR: reading illuminance.** 15–30 lux at 25–30 cm. Either reposition the product as an ambient / night moon, or add a directional downlight (§5.2). This is Matt's decision.
- **F7 MAJOR: wrong RGB data in `gen_modes.py`.** Wrong part and wrong current; the candle and orange colours are wrong. Regenerate (§5.3). Note this goes beyond the planned "30 → 25 mA" update.
- **F8 MINOR: optics model.** Update it to the as-built layout, fix the indirect term, use τ, and report 2-D per-group uniformity. Qualify B4: RGB-only modes give 1.06–1.14.
- **F9 MINOR: night resolution and 2.1 mA operation below the TLC's 5 mA minimum.**
- **F10 MINOR: G/B headroom on battery.**
- **F11 NOTE: flicker compliant.** Keep GRPPWM off.
- **F12 NOTE: margins elsewhere.**
  - LED Tj ≤ 79 °C and TLC Tj ≤ 91 °C (worst, pessimistic, no derating, I_CC max). PETG ≤ 57 °C (61 °C with the gap pad, pessimistic). Moon air 33–44 °C. Lithophane dome about 30 °C.
  - Würth derating: at 25 mA the RGB is allowed to about 59 °C ambient. COOL_6500 (B at 96 % duty, 24 mA average) needs the board ≤ 61 °C. That holds with either curve once derating acts; with the proposed curve it has a wide margin.
- **NOTE: sunlight.** A white PLA moon on a sunny windowsill picks up about 0.4–0.6 W (19.6 cm² × 1000 W/m² × 0.2–0.3 absorptance). That is +5–8 K with the lamp off and adds to everything above. Mention it in the user notes.

## 7. Recommendations (concrete)

1. **Firmware** (`lightcore.h`):
   - `I_CHANNEL_MA 25.0f`.
   - `T_DERATE_START_C 45`, `T_DERATE_KNEE_C 52`, `T_DERATE_MAX_C 58`.
   - Add `I_CAP_UNTRUSTED_MA 110` (VLED ≥ 3.9 V) / 130 (VLED < 3.9 V). Better: compute (0.40 W − VLED × 0.015 A)/(VLED − 1.1 V).
   - Keep `I_CAP_MA 200` only while the sensor is valid and plausible (§4.2 rules).
   - Keep the 30 % NACK fail-safe.
   - Optional: an RC thermal estimator (τ 300 s, 52 K/W), using max(T_sensor, T_model).
2. **LED board v0.1:**
   - LM75B OS → TLC /RESET with 10 kΩ to VLED.
   - Firmware sets Tos 60 / Thyst 52 °C and fault queue 2, and reads back MODE1 to re-init after a trip.
3. **CAD:**
   - Add a PETG clamp ring (or cup lip) that clamps the board band.
   - Have the PLA skirt seat on the PETG step only, with ≥ 0.5 mm air gap above the board.
   - Reconsider CAM_DROP preload on PLA.
   - Add a 2.0–2.5 mm silicone gap pad (≥ 3 W/mK) under the board to the cup floor and nut.
   - Then raise the untrusted cap to 160 mA.
4. **REXT:** keep 750 Ω (25 mA). Revisit 910 Ω only for the G/B-headroom or RGB-derating reasons in §4.3.
5. **Modes:**
   - Regenerate with the Würth and Bridgelux 25 mA data (table in §5.3).
   - Change the "lm" comments to delivered lumens (× 0.6).
   - Raise NIGHT_RED max_level to 15.
   - Give NIGHT_ORANGE and CANDLE low-level recipes that avoid 1-count minor channels.
   - Keep 4000K labelled as a day mode.
6. **Product:** either describe the lamp as ~25–45 lm out (15–30 lux at 30 cm), or add the directional reading LED (§5.2).
7. **Optics model:**
   - As-built geometry, corrected indirect term, τ-based escape output, 2-D per-group metric.
   - Relax B4 to ≤ 1.15, or qualify it as "white modes".
   - Replace ρ/τ with step-wedge measurements (T8).

## 8. Bench test plan (prototype)

**Equipment**
- 8 fine thermocouples (type K or T, 0.08–0.13 mm wire, ≤ 1 mm bead) and a 1 Hz logger.
- Bench supply at 4.20 V and 4.15 V, with an ammeter in VLED at the LED-board end.
- The `attiny3216_debug` build, which logs T / V / cap at 1 Hz.
- A 40 × 40 × 40 cm open-top cardboard draught shield.
- Lux meter (≥ 0.01 lux resolution, or a luminance meter for the night modes).
- Photodiode plus oscilloscope.
- Spectrometer if available.

Fix thermocouples with a dot of thermally conductive epoxy or Kapton tape. Route the leads out through a 1 mm hole drilled in the cup wall, never through the skirt clamp face.

| TC | Location |
|---|---|
| TC1 | Solder point of a CW white LED (D2 cathode pad), board top |
| TC2 | TLC59116 package top |
| TC3 | **PLA skirt bottom face at the clamp band.** Bead in a 0.3 mm groove printed into the skirt, touching the board. This is the pass/fail sensor |
| TC4 | PLA lug root (outer skirt, next to a bayonet lug) |
| TC5 | Moon outer surface just above the cup rim (θ ≈ 50°) |
| TC6 | Moon equator |
| TC7 | Cup outer side wall at mid-height |
| TC8 | Cup bottom next to the M10 nut |
| TC9 | Ambient, shielded, 30 cm away at the same height |

**Tests**

| Test | Procedure | Duration | Pass criteria |
|---|---|---|---|
| T0 Quiescent | All outputs off, VLED 4.20 V: measure I_VLED | 1 min | Record I_CC. If > 20 mA, recompute the caps with the measured value |
| T1 Electrical | Each mode at max level, 4.20 and 4.15 V, cold and after 30 min: measure I_VLED and VLED at the board | 30 min | I_total within ±8 % of the prediction (4000K 182 mA after F3). No channel saturating at 4.2 V |
| T2 Characterisation (open loop, staircase) | Debug build with derating disabled *on the bench only*. All whites at 100 mA, then 150 mA, each to steady state (dT/dt < 0.3 K/10 min, about 45 min each). **Abort if TC3 ≥ 52 °C or TC2 ≥ 90 °C.** Do not run 200 mA open loop | ~2 h | Derive R_PLA = ΔT_TC3/P_board and R_board = ΔT_TC1/P_board. Expected 46 (37–58) and 48 (38–62) K/W. Set the untrusted cap from the measured R_PLA: I_max = (20 K/R_PLA − P_q)/(VLED − 1.1) |
| T3 Release firmware, worst mode | 4000K max level, USB 4.15 V, then battery sim 4.20 V | 2 h each | TC3 ≤ 47 °C; TC4 ≤ 45 °C; TC1 ≤ 70 °C; TC2 ≤ 80 °C; TC7 ≤ 60 °C. Lux at 30 cm logged and settled variation ≤ 2 % per 10 min (no hunting). Record the LM75B − TC3 offset |
| T4 Hot room | T3 inside a 30–32 °C enclosure (warm room or a box with a lamp-heated plate, not the moon) | 2 h | TC3 ≤ 50 °C |
| T5a Sensor NACK | Fault-inject a NACK (debug flag) at full output | 30 min | Output drops to 30 % within 3 s; TC3 ≤ 42 °C at 30 min |
| T5b Sensor stuck low | Fault-inject a constant 25.0 °C reading, then 0x0000 | 2 h | Plausibility trips within 10 min; current ≤ hard cap; TC3 ≤ 47 °C at 2 h |
| T6 Hardware backstop (if fitted) | LEDs at 5 %; heat the board underside with a hot-air pencil until LM75B ≥ 60 °C | 10 min | LEDs off within 1 s of OS; resume after < 52 °C and firmware re-init |
| T7 Creep / fit | Before and after T3 + T4, and after 10 cycles of 2 h on / 1 h off: measure skirt bottom flatness, lug height and skirt OD (calipers ±0.02 mm), and check bayonet engagement and wobble | 30 h | No permanent change > 0.05 mm; no loosening; lugs uncracked |
| T8a Wall optics | Step wedge 0.6 / 0.9 / 1.2 / 1.6 / 2.0 / 2.6 / 3.0 mm in the production PLA and profile, over each channel in a dark box | 1 h | Measured τ(t) and ρ(t). Replace ρ/τ in the model. Expect τ(1.75 mm) ≈ 0.2 |
| T8b Total flux | Illuminance at 1.0 m in 12 directions (30° steps, two meridians), integrated, at 4000K full cold | 30 min | Φ_out = 39 lm ± 20 %. If < 31 lm, PLA absorption is higher than assumed (more heat in the wall, less light) |
| T8c Page | 4000K full: E at 25 and 30 cm, α = 30° and 45°, at t = 0 and 30 min. Night modes at max level: E at 30 cm, or luminance (cd/m²) at the moon | 1 h | Within ±30 % of §5.2 / §5.3 |
| T8d Uniformity | RAW photos at fixed exposure in WW-only, CW-only, red-only and all-white; compare with an unlit transmitted-light image | 30 min | No visible 4-fold or 2-fold pattern above the collar beyond the lithophane image; a dark collar band is expected |
| T9 Flicker | Photodiode + scope at levels 0, 3, 8, 15 for each mode, on USB and at VLED 3.6 V; also during slow fades across CG steps | 30 min | Only 97.6 kHz content; no component < 3 kHz; no visible step > 2 % at CG transitions |
| T10 Colour | Spectrometer per mode after regeneration | 30 min | Whites within 3 SDCM / Duv ±0.003; candle Duv ±0.005; orange mel DER ≤ 0.15 |

Bench outcomes that change the recommendations:
- If T2 measures R_PLA > 55 K/W, set the untrusted cap to 90 mA and the curve to 42/50/56.
- If T0 finds I_CC ≥ 25 mA, cut the cap by 10 mA.
- If T8b finds escape < 0.55, more heat goes into the shell and less light comes out. The PLA clamp rating barely changes; it is board-dominated.
