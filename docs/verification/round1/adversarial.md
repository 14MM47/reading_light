# Adversarial safety and reliability review: moon reading light v0.1

Reviewer role: adversarial (safety and reliability). Date: 2026-11-02. No repo files were edited.

**Inputs read**
- Hardware: `hardware/main-board/design.py` (including the MOUNT_HOLES added during the review), `hardware/led-board/design.py`, `hardware/parts.py`, and both `reports/*.net` netlists (the netlists match design.py).
- Firmware: `firmware/src/main.cpp`, `lib/core/lightcore.{h,cpp}`, `include/*.h`, `tools/gen_modes.py`, `test/test_core`, and the megaTinyCore 2.6.11 Wire library.
- CAD: `cad/parts/moon_shell.py`, `moon_base.py`, `pack_front.py`, `_lib/moonlib.py`, `_lib/packlib.py`.
- Optics: `docs/design/optics/sphere_illum.py` and its output.
- Plan and research: `PLAN.md`, `docs/research/neck-battery-pcb-pricing.md`.
- Datasheets in `scratchpad/ds/`, plus `KEYSPECS.md`.

**Calculations**
- My scripts: `scratchpad/review/adv_calc/adv_thermal.py` (lumped moon-head model) and `adv_calc/modes_check.py` (mode colour and flux using the LEDs actually on the board).
- The thermal model is order-of-magnitude only: ±10–15 K. Every temperature below is an **estimate to be measured** with a thermocouple on the board edge and on the PLA skirt.

Severity scale:
- **BLOCKER**: fix before first power-on, print or use.
- **MAJOR**: fix in v0.1, or before anyone else uses the light.
- **MINOR**: fix when convenient.
- **NOTE**: claim check or information.

---

## 0. Summary table

| ID | Sev | Area | One line |
|---|---|---|---|
| B-1 | BLOCKER | FW / thermal | After an "empty" sleep, the firmware resets itself but leaves the LM75B in shutdown. It then reads a frozen temperature for good, so **thermal derating is silently disabled**, typically while running on USB. |
| B-2 | BLOCKER | Pack / LiPo | The M2 screw heads on the PCB's back face point at the pouch. The heads are ≈1.6 mm high in a 1.3 mm gap, so they **press into the LiPo pouch** with zero swelling margin. J4 pins would add another 3 mm. |
| B-3 | BLOCKER | Pack / LiPo | The face of battery header J2 is 0.5 mm from the board edge and 0.85 mm from the enclosure wall. **The PH plug and leads cannot fit.** The battery lead has no defined route past a PCB edge with 0.35 mm clearance, so it will be pinched. |
| M-1 | MAJOR | Thermal / FW / HW | The temperature sensor and the LED driver share one I²C bus and one cable. There is no watchdog, and the MCU cannot reset or unpower the TLC59116. A hang, stuck bus or chafed wire **latches the LEDs with no thermal control** (board ≈60–75 °C). |
| M-2 | MAJOR | Thermal / mech | The derating thresholds (50/65/75 °C) let the board settle at ≈55–61 °C. **The PLA skirt clamps the board edge**, so it sits at or above PLA's heat-deflection temperature (HDT) all the time: creep, a loose moon, deformed lugs. The "0.6 W budget" is not PLA-compatible. |
| M-3 | MAJOR | LiPo | Left switched on, "empty" puts the MCU to sleep but the TLC59116 stays powered (I_CC up to 25–29 mA max). The cell is pulled to the PCM's 2.4 V cut-off in hours, then sits deeply discharged. The MCP73831 will recharge it from any voltage. |
| M-4 | MAJOR | LiPo | Charging is not temperature-qualified: no NTC, no timer. The charger dissipates 0.5–0.9 W (in thermal regulation, die >100 °C) **1.3 mm above the pouch**, and will charge happily below 0 °C. |
| M-5 | MAJOR | USB | Nothing protects against VBUS over-voltage. The SMF5.0A clamps at about 9 V, above the MCP73831's 7 V absolute maximum. A bad or fixed-voltage source destroys the charger, MCU and driver, leaving the **PCM as the only barrier to overcharge**. |
| M-6 | MAJOR | USB / short | Nothing protects the USB→D3→VSYS→cable path against overcurrent. A short in the neck or at the LED pads puts 2–3.5 A of source current through a 1 A SMA rectifier (3–4 W) sitting **over the pouch**, and through 28 AWG wire and a 1 A JST-SH. |
| M-7 | MAJOR | Mech / cable | The moon cable has no abrasion protection inside the spiral-wound neck or at the cut thread ends, and no strain relief at the LED-board pads (2.2 mm cavity) or at the JST-SH, which has no positive latch. This is the initiating event for M-1 and M-6. |
| m-1 | MINOR | LiPo | With USB connected, a reversed cell is **not** blocked. Q3 runs linear and discharges the cell at the 42 mA precondition current, with 0.19 W in Q3, while the charge LED shows "charging". |
| m-2 | MINOR | Power | On USB unplug, VSYS runs through Q1's body diode for ≈0.4 s because VBUS decays through 100 kΩ. At mid-to-low battery this causes a brown-out, TLC under-voltage and a possible BOD reset. |
| m-3 | MINOR | FW | `I_CHANNEL_MA` is 30.2 mA (from a 620 Ω REXT) but the hardware uses 750 Ω, giving 25.2 mA. The cap is really ≈166 mA. The comments and the "~0.6 W" note are stale, and "fixing" REXT to match would overdrive the RGB. |
| m-4 | MINOR | FW | IREF and the PWMs are written in separate transactions, in the wrong order. This gives a ≈2 ms current step of up to 2× (a visible flash). |
| m-5 | MINOR | FW | There is no TLC/LM75B register read-back, no plausibility check, no bus recovery, and `tlc_ok` never drops. A power-glitched TLC stays dark until the light is power-cycled. |
| m-6 | MINOR | ESD | The touchable metal neck reaches within ≈1–2 mm of the TLC59116 pins (1.5 kV HBM). SDA, SCL and the buttons have no ESD parts. |
| m-7 | MINOR | Mech | The neck is self-tapped into PETG, with "thread-locker" (an anaerobic adhesive won't cure against plastic and can craze it). Unlocking the moon's bayonet is in the direction that unscrews the base cup, which twists the cable. |
| m-8 | MINOR | Pack | The clip and back plate are not designed yet. The pouch must not become a structural member. The 0.6 mm swell allowance is fine for ageing, but the enclosure must give way, not crush the pouch, if the cell gasses. |
| m-9 | MINOR | FW | The VDD measurement relies on INT1V1, ±2 % (±5 % above 3.6 V). The battery thresholds are therefore only good to about ±70 mV. Calibrate. |
| N-1…N-12 | NOTE | Claims | R17 drain (passes on paper), lumens and colour (RGB data are for the wrong part), optics model geometry, reading illuminance, RGB derating, BOD versus clock, charge parameters, USB budget, child safety, flammability, things that held up. |

---

## 1. BLOCKERS

### B-1 BLOCKER: LM75B is left in shutdown after the "empty" sleep, so thermal derating is defeated

**Scenario**
1. The light runs flat with the slide switch on.
2. `sleep_until_resumed()` writes LM75B config register 0x01 = 0x01 (shutdown).
3. The user plugs in USB, so VDD rises above 3.7 V.
4. The firmware calls `_PROTECTED_WRITE(RSTCTRL.SWRR, …)`, a software reset of the **MCU only**. VSYS never drops, so the LM75B does not see a power-on reset.
5. `setup()` never writes the LM75B config register back to normal mode (`main.cpp` 145–163).

**Consequence**
- The LM75B datasheet (Rev. 6.1, p5) says: "In shutdown mode, the device becomes idle, data conversion is disabled and the Temp register holds the latest result; however, the device I²C-bus interface is still active".
- So `lm75_read()` keeps returning `ok = true` with the **last temperature measured before shutdown**. That reading was taken at the end of a fade-out at `LOW_CAP`, so it is warm but below 50 °C, and `thermal_factor` = 1.0 for good.
- The failsafe never triggers, because the reads succeed.
- This lasts until the slide switch is cycled. It is the exact sequence "battery flat, plug in USB, keep reading", and on USB VLED is at its highest (4.15–4.45 V).
- Estimated board temperature at the 166 mA cap, VLED 4.15–4.45 V, 25 °C ambient: **60–75 °C** (adv_thermal.py: optimistic 59.5, central 64.6/68.1, pessimistic 70.7/74.6).
- At that temperature the PLA skirt is above its HDT (M-2), and the RGB LED exceeds the Würth derating curve, which allows 25 mA only up to 58.8 °C (see N-5).
- The bug sits in untested glue code: `test/test_core` covers only `lightcore`.

**Mitigation (firmware, zero cost)**
1. In `setup()`, write LM75B config = 0x00 every time, then read it back. Treat a mismatch as a sensor fault (failsafe cap).
2. Simpler still: delete the LM75B shutdown write. It saves about 100 µA, while the TLC59116 draws mA in the same state (see M-3).
3. Add a staleness check: if the temperature register is bit-identical for more than 60 s while the drive is above 20 %, treat the sensor as failed.
4. Add a host test that models "sensor frozen".

### B-2 BLOCKER: PCB screw heads and through-hole pins face the LiPo pouch with negative clearance

**Evidence**
- `packlib.py` stacks the parts as: back plate (1.8 mm), battery bay T = 5.6 for a 5.3 mm pouch, `BAT_SWELL` 0.6, then +0.4 mm to `Z_PCB_BOT`.
- So the gap from the nominal pouch top to the PCB's back face is 5.6 − 5.3 + 0.6 + 0.4 = **1.3 mm**.
- `pack_front.py` docstring: "M2 self-tapping screws **from the PCB's back**". `design.py` adds `MOUNT_HOLES` at (21.5, 10.0) and (17.5, 46.5).
- An ST2.2 or M2 pan head (DIN 7981 / ISO 7045) is k ≈ 1.6 mm high. That is **0.3 mm of interference with a new pouch**, and the 0.6 mm swelling allowance is used up at exactly those two points.
- `J4` (UPDI header, "pins fitted only for programming") is through-hole. If its pins are left in, they protrude about 3 mm out of the back face, straight into the pouch.
- Book-clip loads and swelling then press the pouch onto these points (see also m-8).

**Consequence**: a point load or puncture on a LiPo pouch, the classic cause of an internal short and thermal runaway. The cell is the one part of this product that can start a fire.

**Mitigation** (pick one; all are cheap)
- **(a)** Make the board stand-off from the pouch side impossible: put the bosses on the back plate, with screws entering from the component side through 2.5 mm holes, so the heads are on top. Or use snap or heat-stake retention from the front shell with ribs, so nothing is on the back face.
- **(b)** Add a flat separator between the cell and the PCB: 0.5 mm FR4, PC sheet or a printed 0.6 mm shelf, with clearance pockets for the screw heads. Keep ≥ 0.6 mm of free swell space above the separator. This costs about 2 mm of thickness; 17.4 → ~19.4 mm still meets R22 (≤ 20 mm).
- Add a rule: "no through-hole part, screw tip or solder spike on the back face". Check this in the CAD claims (a "pcb_back_clear ≥ swell" claim).
- J4: use pogo pins or a Tag-Connect footprint, or state in the build notes that the header must never stay fitted. Clip back-face THT leads flush (the USB-C shell slots).

### B-3 BLOCKER: the battery plug and leads have no space; the lead route pinches at the PCB edge

**Evidence**
- J2 (S2B-PH-SM4-TB, side entry) sits at (4.9, 54.5) rotated −90°. The fab outline puts its mating face at footprint y = +4.4, which is board x = **0.5 mm** from the left edge.
- `packlib.CLEAR` = 0.35 mm from PCB edge to inner wall. That leaves **0.85 mm** for a PHR-2 plug, which must be inserted from that side, protrudes several mm past the header face, and needs room for its wire exit and bend.
- `pack_front.py` has no pocket there.
- The pouch lies **under** the PCB, but J2 is on the **top** face. A ~100 mm lead must pass a PCB edge that has 0.35 mm of clearance on three sides; only the top neck region, 11 mm, is open.

**Consequence**
- The pack cannot be assembled without forcing the plug or crushing the lead.
- The likely outcome is a lead pinched between the FR4 edge and the wall.
- Those leads are protected only by the cell's PCM. A partial, resistive short heats without tripping it.

**Mitigation**
- Add a plug-and-lead pocket at least 8 mm beyond the J2 face.
- Define the lead's path from the pouch's PCM end to J2 with a channel, ≥ 1.5 mm clear and with radiused edges. Add CAD claims for both.
- Or turn J2 so the plug enters toward the neck region, which has space, and route the lead there.
- Add the note "VERIFY the PCM end and lead exit of the received cell".

---

## 2. MAJOR

### M-1 MAJOR: there is no independent thermal or overcurrent backstop for the moon head

**Scenario A**: the MCU hangs. There is no watchdog: `platformio.ini` sets no `WDTCFG` and the code has no `wdt_*`.

**Scenario B**: the I²C bus stops working.
- Possible causes:
  - SDA or SCL shorted to VSYS or GND by chafe in the neck (M-7).
  - A half-unplugged JST-SH.
  - A slave holding SDA.
  - ESD.
- megaTinyCore 2.6.11 Wire has `TWI_TIMEOUT_ENABLE`, so the MCU does not hang. But nothing can reach the TLC59116 either.
- The temperature reads fail, and after 3 s `core_temperature` sets `T_FAILSAFE_CAP`. That cap **cannot be delivered, because it travels over the same dead bus**.
- On the LED board, /RESET is tied to VLED, so the MCU has no hardware means to switch the LEDs off.

**Scenario C**: bus corruption (ESD or a bit error into the auto-increment write at 0x02) lands in LEDOUT = 0x55 ("fully on") or 0xFF with GRPPWM = 0xFF. All 14 channels then run at full scale.

**Consequence**: the TLC59116 holds its last state indefinitely. TSD is 150 °C at the junction (min), so it never acts at these board temperatures.

| Latched state | Current | Board estimate, 25 °C ambient (adv_thermal.py) |
|---|---|---|
| Firmware cap, 166 mA actual, VLED 4.15–4.45 V | 166 mA | **59–75 °C** (central 65–68 °C) |
| Hardware maximum: 14 × 25.2 mA, +8 % tolerance | 353–381 mA (1.5–1.8 W input) | **93–125 °C** |

- In the firmware-cap case, the PLA skirt is above its HDT and the RGB is above its derating curve.
- In the hardware-maximum case:
  - The PLA skirt softens and the moon loosens or deforms.
  - The PETG cup is above its Tg (~80 °C).
  - The Würth RGB is beyond its 85 °C operating limit.
  - The Bridgelux LEDs exceed Tsp 105 °C.
- No ignition is credible (PLA and PETG auto-ignite above 350 °C). But a hot, deforming head over a bed or a child's book is a real hazard, and the moon is twist-off (N-9).

**Mitigation** (cheap, layered)
1. **Hardware thermostat, zero BOM cost.**
   - Wire the LM75B OS pin (U2.3, currently unconnected) to TLC59116 /RESET (U1.25).
   - Replace the /RESET-to-VLED tie with 10 kΩ to VLED.
   - At power-up the LM75B is a stand-alone thermostat: comparator mode, active low, Tos 80 °C, Thyst 75 °C. It needs no I²C and no MCU.
   - At boot the firmware writes Tos ≈ 60 °C, Thyst ≈ 50 °C and fault-queue 2, then reads them back. Put Tos below the PLA limit once M-2 is settled.
   - A trip resets the TLC to its power-on defaults (all outputs off, OSC off), so it **fails dark**. The firmware sees MODE1 = 0x91 on read-back and re-initialises after cooling.
   - TLC VIL = 0.3·VCC ≈ 1.25 V. The LM75B OS VOL is ≤ 0.4 V at 3 mA, against a 0.42 mA load from the 10 kΩ pull-up. OS leakage is ≤ 10 µA when not tripped. All compatible.
2. **MCU-controlled feed to the moon.**
   - Add Q4, a DMG2305UX (already in the BOM), as a high-side switch between VSYS and J3 pin 2.
   - Drive its gate from a spare pin (PA7 or PB2…PC3 are free) with a 100 kΩ pull-up to VSYS, so it is off during reset and BOD. Slew-limit the gate (10 kΩ series and 47 nF G–S) so inrush into ≈15–20 µF does not dip VSYS.
   - Move R8/R9 (the I²C pull-ups) to the switched rail, so the TLC is not back-powered through its input clamps when off.
   - With this, any watchdog reset, brown-out or stuck bus removes LED power and power-on-resets the TLC. It also fixes M-3.
3. **Fuse-locked watchdog.** Set `WDTCFG` PERIOD to 1–2 s, then call `wdt_reset()` only from the main loop after a successful sensor read **and** TLC read-back. The PIT wake in the empty loop must also reset it.
4. **Bus recovery.** Clock 9 SCL pulses with SDA released, then STOP, on any `TWI_ERR_*` or timeout. After N failures, power-cycle the moon through Q4.

### M-2 MAJOR: the derating thresholds and thermal budget are incompatible with a PLA clamp on the board

**Evidence**
- `moonlib.py` / `moon_shell.py` B7: "a 2.5 mm skirt … its bottom face **clamps the LED board edge band**". The board's copper pours run out to r = 12.0 mm, and the clamp band is r 12–13 mm.
- With 1 oz copper on both layers, the radial drop from the centre to the clamp is only ≈2–3 K. So the PLA skirt and lugs sit at roughly the LM75B temperature (the LM75B is at r ≈ 8.3 mm).
- `CAM_DROP` 0.35 mm puts the clamp under a permanent preload.
- Material limits (typical datasheet values; VERIFY against `config/materials.toml`):
  - PLA: Tg ≈ 55–60 °C, HDT at 0.45 MPa ≈ 52–57 °C.
  - PETG: HDT ≈ 68–70 °C.

**Firmware equilibrium** (lumped model, derating 50/65/75 °C, 166 mA all-white, USB):

| Ambient | Board (central model) | Board (pessimistic model) | Brightness, % of cap |
|---|---|---|---|
| 25 °C | 55.7–56.7 °C | 57.4–58.3 °C | 61–74 % |
| 30 °C | 57.4–58.3 °C | 59.0–59.8 °C | 54–65 % |
| 35 °C | 59.2–60.0 °C | 60.5–61.3 °C | 47–57 % |

So in normal use the controller holds the PLA **at its HDT for hours**. Expect, in rough order of timing:
- creep of the skirt clamp (the board rattles, light leaks round it);
- creep of the 0.8 mm bayonet lugs, so the moon loosens or drops when pointed down;
- sag of the near-base lithophane collar.

The comment `I_CAP_MA 200 // moon-base thermal budget, ~0.6 W` is unverified. At the real 166 mA the input is 0.67–0.81 W and 0.49–0.62 W of it is heat in the head.

**Mitigation**
- **Mechanical:** make the **PETG cup** clamp the board, for example a PETG retaining ring under the bayonet. Keep PLA ≥ 1 mm away from the board, with an air gap, and clamp only on the unplated band.
- **Thresholds:** if PLA must touch the board, lower them to about 40/48/55 °C. The model then gives 46–50 °C at 25–35 °C ambient, but sustained brightness falls to **25–46 % of cap**. That is a real light-output trade-off, so record it as a decision.
- **Better heat sinking:** an aluminium or copper spreader disc, with a thermal pad from the TLC side to the M10 nut and the gooseneck, raises the sustained budget.
- **Measure:** use a thermocouple on the skirt and compare it with the LM75B reading.
- **Thermal headroom:**
  - Reduce VLED headroom on USB, since TLC dropout is 0.29–0.35 W of the heat on USB.
  - Use a Schottky with a separate off-switch, or put a series PTC or resistor in the moon feed. Even 0.5 Ω cuts the driver heat by 14 mW per 166 mA.

### M-3 MAJOR: the LiPo is over-discharged if the light is left switched on

**Evidence**
- At "empty" (VDD < 3.30 V for 5 s), `sleep_until_resumed()` writes PWM = 0 and OSC off, then puts the MCU in power-down.
- **VLED stays connected.** TLC59116 I_CC with outputs off is specified only as a maximum: 25 mA (REXT open) to 29 mA (720 Ω) at VCC 5.5 V. No standby figure is given, and "standby" (all outputs off) uses that same specification.
- The Pimoroni BAT0004 PCM cuts off at **2.4 V**.
- At 3.30 V under load, about 3–5 % (≈40–60 mAh) is left. At 5–25 mA the cell reaches the PCM cut-off in roughly **2–12 h**.
- After that the PCM's own drain and self-discharge carry it lower over weeks or months in a drawer.
- MCP73831: preconditions at 10 % of IREG (42 mA) for any VBAT < 2.79 V. It has no dead-cell lockout and no timer.
- Charging a cell that has sat below ~2 V risks copper dendrites and an internal short.

R17 covers only "slide switch off". The realistic failure is "switch left on". R5 makes the main button unable to turn the light off, so the slide switch is the only off control and people forget it.

**Mitigation**
- Fit Q4 from M-1 and cut the moon feed at "empty". Board drain then falls to ≈1–3 µA: MCU power-down with PIT ≈1 µA, plus pull-ups on the switched rail.
- Optionally add a latching UVLO on Q2's gate, for example a supervisor such as TPS3839 or MCP111 at ≈3.0 V, so the pack is cut off in hardware below 3.0 V.
- User note: "switch off after use; recharge within a month; if the pack has sat flat, measure VBAT at TP2 and do not recharge if it is below 2.5 V".

### M-4 MAJOR: charging is not temperature-qualified, and the charger heat sits over the pouch

**Evidence**
- MCP73831 dissipation is (VBUS − VBAT) × IREG:
  - (5.0 − 3.0) × 0.417 = 0.83 W at the start of CC;
  - 0.54 W at 3.7 V;
  - up to 0.94 W at 5.25 V.
- In SOT-23-5, θJA is 130–230 K/W. The die reaches its thermal-regulation region (Fig. 4-2 folds back towards 150 °C), so it runs above 100 °C for the first part of every charge.
- U1 is at (29, 51). The whole PCB lies 1.3 mm above the pouch (B-2), with no thermal barrier.
- The local pouch temperature is likely to exceed the usual 45 °C charge limit. This is an estimate; VERIFY with a thermocouple taped to the pouch under U1.
- There is no NTC (the Pimoroni and Adafruit cells have none) and no charge timer, so charging also proceeds below 0 °C (lithium plating).
- The pack also holds D3, which dissipates 0.14 W on USB with the light on.

**Mitigation, cheapest first**
1. Change R3 from 2.4 kΩ to **4.7 kΩ** (IREG ≈ 213 mA, ≈0.18 C). This halves the heat to 0.27–0.48 W, and a full charge takes ≈6.5 h, which is acceptable for a bedside lamp.
2. Add a 0.3–0.5 mm insulating pad (polyimide tape or closed-cell foam) on the PCB's back face under U1, D3 and Q1–Q3, inside the B-2 gap budget.
3. Proper fix:
   - Use a charger with a TS input and a timer, e.g. TI **BQ21040DBVR** (SOT-23-6; 30 V-rated input with ≈6.6 V OVP, which also helps M-5; VERIFY on the datasheet).
   - Add a 10 kΩ β3435 NTC on a flying lead taped to the pouch, e.g. Murata NXFT15XH103FA2B.
4. User note: "do not charge below 5 °C or above 40 °C; do not charge in a closed bag or under a pillow".

### M-5 MAJOR: VBUS over-voltage

**Evidence**
- The sink has 5.1 kΩ Rd only and no D+/D−, so compliant PD and QC chargers stay at 5 V. Faulty chargers, fixed-voltage "USB-C" barrel adapters (9/12/20 V) and damaged cables do exist.
- D1, the SMF5.0A (datasheet not retrieved; typical family values), is a transient clamp: VBR ≥ 6.4 V, VC ≈ 9.2 V at IPP. It is not a DC regulator.
- Absolute maximums on the path: MCP73831 VDD **7.0 V**, ATtiny 6.0 V, TLC59116 7.0 V, LM75B 6.0 V, DMG2305UX VGSS ±8 V.
- What a sustained 9 V input does:
  - D1 conducts amps and fails, usually short, which is the good case; or it fails open.
  - The charger's pass device can fail short, so VBUS is applied to the cell, limited only by the source.
  - D3 puts about 8.2 V on VSYS: the MCU and TLC are destroyed, and Q2's VGS reaches −8.2 V, beyond its rating.
- The cell's PCM overcharge detector becomes the **only** barrier. That inverts the pcb-repo rule that the protection IC must be the second backstop, never the primary.

**Mitigation**
- An input OVP load switch ahead of the split, rated ≥ 20 V in and ≥ 0.8 A, in SOT-23 or TSOP to respect R21. For example onsemi NCP361SNT1G (TSOP-5, OVLO ≈ 5.7 V). VERIFY its current rating, or choose an equivalent.
- At minimum, add a **PTC on VBUS ahead of D1**, e.g. Bourns MF-MSMF075-2 (1812, 0.75 A hold). The TVS then becomes a crowbar that trips the PTC, which also serves M-6.
- Pair either with the BQ21040 from M-4.

### M-6 MAJOR: no current limit on the USB→VSYS path or the moon cable

**On battery**
- Path resistance: cell ≈0.1–0.15 Ω, PCM ≈0.05, Q3/Q1/Q2 ≈0.06 each, JST and traces, plus 2 × 0.15 m of 28 AWG (0.064 Ω). Total ≈0.45–0.5 Ω, so ≈7 A.
- The DW01-class PCM detects over-current (≈150 mV across its FETs) and trips in about 10 ms. The FETs survive (IDM −15 A). **Acceptable.**

**On USB**
- Q1 is off, and its body diode feeds the short only until the PCM trips. After that, **D3 (S1J, 1 A)** carries whatever the source delivers before its own OCP: typically 2–3.5 A, and some cheap adapters deliver more.
- S1J VF at 3 A is ≈1.1–1.2 V, so it dissipates **3.3–3.6 W in an SMA package, directly over the pouch**.
- The 28 AWG wires (0.21 Ω/m) dissipate ≈2 W/m inside a metal tube. JST-SH is rated 1 A.
- The likely sequence is D3 overheating and failing (often short), scorching the PCB 1.3 mm above the cell.

**Mitigation**
- The VBUS PTC from M-5.
- Optionally a 0.3–0.35 A PTC in J3 pin 2, sized for the 166 mA cap plus about 30 mA of driver current (e.g. a Bourns MF-NSMF or MF-PSMF 0.35 A part; check R1max ≤ 1.5 Ω and Vmax ≥ 6 V). Its drop also trims TLC dropout heat (M-2).
- Or let Q4 (M-1) act as an electronic fuse: the firmware turns it off when VSYS sags while the LEDs are being driven.

### M-7 MAJOR: moon cable abrasion and strain relief

**Inside the neck.** The 6.8 mm bore of a spiral-wound gooseneck has strip edges that abrade 28 AWG PVC insulation (≈0.2 mm wall) with every bend. The cut M10 thread ends are sharp and unbushed at both ends.

**At the LED board**
- The four stranded wires are soldered to J1 pads (2.0 mm pitch) on the underside, inside a **2.2 mm** cavity above the nut, with the TSSOP and 0805 parts (≤1.3 mm) beside them.
- They turn 90° right at the joint, where the stiff solder-wicked section is the classic fatigue break point.
- The pad pitch invites stray strands to short VLED to GND.

**At the pack**
- JST-SH has a friction lock only.
- A tilted partial unplug opens pin 1 (GND) or pin 4 (SCL) first. With GND open and VLED connected, the LED board's return current flows through the TLC and LM75B input clamps into SDA and SCL, and into the ATtiny pins (±40 mA absolute maximum).

**Assembly.** The cable already passes through the cup when the cup is threaded onto the neck, so every turn of the cup twists the bundle.

**Consequences**
- Intermittent flicker.
- A stuck or corrupted bus (M-1: latched LEDs).
- A VSYS short (M-6).
- Damaged MCU or TLC pins.

**Mitigation**
- Use PTFE-insulated wire (abrasion-resistant), or run the four wires in a PTFE or PVC inner sleeve (≈3–4 mm OD) for the whole neck length.
- Fit grommets or bushings at both thread ends: a printed PETG top-hat in the nut bore.
- On the LED board, add strain-relief holes (wire passes up through a ≥1.0 mm hole and back down to the pad) plus a dab of hot-melt or epoxy.
- In the pack, anchor the cable with a printed clamp or cable-tie point before J3, and leave a service loop. Or use a latching connector (JST GH 4-pin) or soldered pads with strain relief.
- Assemble in this order: cable through the neck, cup fixed, then solder the board. Or rotate the cup the other way first to pre-twist.

---

## 3. MINOR

**m-1 Reverse battery with USB connected.**
- With USB connected and the cell reversed (cell + on GND), the charger output BAT sits above GND while Q3's gate is at GND. Q3 conducts in its linear region, settling at BAT ≈ |VGS(th)| ≈ 0.5–0.9 V.
- The MCP73831 sees VBAT < 2.79 V and **preconditions at 42 mA**. Current flows into the reversed pack's "−" lead, which the PCM sees as ordinary discharge.
- Q3 dissipates ≈(0.7 + 3.7) × 0.042 ≈ 0.19 W.
- The light works normally from USB, and the red LED says "charging". After ~28 h the cell reaches the PCM's 2.4 V and is left reversed and flat.
- So the comment "Q3 blocks a reversed battery" holds **only without USB**.
- Mitigation:
  - Make metering every pack a mandatory build step (the research note says about half of vendors reverse the polarity).
  - Optionally fit a reverse-polarity indicator: red LED + 1N4148 + 1 kΩ from GND to BAT_RAW, which conducts only when reversed. The 1N4148 keeps leakage at nA, protecting R17.

**m-2 USB-unplug brown-out.**
- C1 (≈7 µF effective) discharges through R5 (100 kΩ) after the charger's UVLO. Q1 stays off until VBUS < VSYS_RAW − |Vth|, which takes ≈0.3–0.4 s.
- In that window VSYS is fed through Q1's body diode, about 0.7 V down.
- At VBAT 3.5 V and 166 mA, VSYS ≈ 2.75 V. That is below the TLC59116's 3.0 V minimum, at the white LEDs' cut-out, and inside the BOD band (2.4–2.9 V), so the MCU may reset.
- Mitigation: R5 → 10 kΩ (0.5 mA while plugged in), or drive Q1's gate from a comparator. Firmware: re-initialise the TLC when VSYS dips.

**m-3 Firmware current constant mismatch.**
- `lightcore.h` has `I_CHANNEL_MA 30.2f // REXT 620 R`. The board uses R1 = 750 Ω, giving 1.26/750 × 15 × 0.992 = **25.0 mA**.
- So the cap `I_CAP_MA 200` really limits at ≈166 mA. That is conservative, which is fine.
- But `gen_modes.py` ("30 mA"), the lumens, the "~0.6 W" comment and the tests are all built on 30 mA.
- The danger is someone later "aligning" REXT to 620 Ω: RGB at 30.2 mA exceeds Würth's 30 mA absolute maximum and its derating above 50 °C.
- Set `I_CHANNEL_MA 25.0f` and derive it from `hardware/led-board/design.py`, the same way `board_map.h` is generated.

**m-4 IREF/PWM write order.**
- `tlc_output()` writes IREF in one transaction and the PWMs in the next. On a gain step up (×2, or up to ×12 on a mode jump), the old PWMs run at the new gain for ≈2 ms.
- That is a visible flash, and the total can briefly exceed the cap.
- Fix: when the gain goes up, write the lowered PWMs first and IREF second; reverse the order when it goes down. Or write PWM…IREF in one auto-increment burst, with OCH = 0 so outputs update on STOP.

**m-5 Driver and sensor state are never verified.**
- `tlc_ok` never returns to false. If the TLC power-cycles (connector glitch, brown-out, or the reset from M-1's OS link), it comes back with OSC off and LEDOUT = 0. The firmware's `last_pwm` cache suppresses re-writes, so the lamp stays **dark** until power-cycled. This fails safe, but it is a reliability bug.
- Read back MODE1 and LEDOUT every second and re-init on mismatch.
- Reject LM75B values outside −20…+125 °C, and step changes > 5 K/s.
- Add I²C bus recovery (see M-1).

**m-6 ESD.**
- The touchable steel neck's thread end sits in the 2.2 mm cavity, ≈1–2 mm below the TLC59116 pins. The TLC is centred over the bore and rated **1.5 kV HBM**.
- Würth RGB is rated 1 kV HBM. There are no series resistors or clamps on SDA/SCL, and the PTS645 metal frame floats behind 7 mm printed caps.
- Mitigation:
  - Specify "thread end flush with or below the nut".
  - Fit a 0.25 mm polyimide or PETG insulating disc between the nut and the board.
  - Add 100 Ω in series with SDA and SCL at J3 and at the LED pads, plus a low-capacitance dual TVS on SDA/SCL at J3 (e.g. Nexperia PESD5V0S2BT, SOT-23).
  - Make the button caps with a long skirt for creepage.

**m-7 Neck mounting.**
- **Pack end:** the M10×1 neck self-taps into a 9.3 mm PETG socket (≈7–8 mm of engagement), "plus thread-locker". Anaerobic thread-lockers cure poorly unless both surfaces are metal, and some craze thermoplastics. Every adjustment torque and every bayonet twist acts on this joint, so it will loosen and rotate over time, twisting the cable. Use epoxy or a captured nut or plate; anti-rotate the neck with a flat or pin.
- **Moon end:** the bayonet locks clockwise seen from above, so **unlocking is counter-clockwise, the direction that unscrews the base cup's nut** (the nut sits in a hex socket and turns with the cup). Reverse the bayonet hand, or fix the nut to the thread with epoxy or a second lock-nut below the floor.

**m-8 Pack, clip and pouch loading.**
- The clip and back plate do not exist yet. Requirement: the clip's root and the book-cover reaction must be carried by the shell walls, not by the 1.8 mm back plate over the pouch. A 4-edge-supported PETG plate deflects ≈0.2 mm per 10 N at its centre; unsupported spans deflect much more.
- The pouch must never be the load path.
- `BAT_SWELL` 0.6 mm (11 %) covers normal ageing. For abnormal gassing, design the back plate to pop off (tabs plus 2 screws) rather than crush the pouch onto the PCB.
- Keep the bay's 0.25 mm side clearance away from sharp corners; radius every bay edge ≥ 0.5 mm.

**m-9 Battery thresholds rest on INT1V1.**
- VDD = 1.1 V × 1023/RES. INT11V is ±2 % for VDD 1.8–3.6 V at 0–105 °C, and ±5 % across the full range (Table 36-23).
- So the "empty 3.30 V" threshold can be 3.23–3.37 V. The "low" threshold, and the 3.7 V "resume", which is taken above 3.6 V, can be ±5 %, i.e. ±0.19 V.
- No safety impact because of the PCM, but calibrate per unit at TP3 with a meter and store a factor in USERROW.

---

## 4. NOTES and claims check

**N-1 R17 "switch off: standby drain < 10 µA": passes on paper.**
- With the switch off, Q1 stays on (gate = VBUS ≈ 0 V via R5), so VSYS_RAW is live.
- R6 and R7 are both at VSYS_RAW, so they pass no current.
- Remaining leakages:
  - MCP73831 IDISCHARGE: 0.25 µA typ, 2 µA max with VDD floating.
  - Q2 IDSS: ≤ 1 µA at −20 V, far less at −4 V.
  - S1J reverse leakage at 4 V into R5: nA typical.
- Total ≈0.3 µA typical, ≤ 3 µA worst case at 25 °C, plus the cell PCM's own few µA.
- The decision to use S1J over MBR120 (0.6 mA leakage) is correct.
- No "zero drain" claim exists in the repo. The real drain problem is "on and empty" (M-3).

**N-2 Lumens and colour claims are wrong for the built hardware.**
- `gen_modes.py` uses 12 / 13.5 lm per white LED at 30 mA. The datasheet gives ≈20 % of the 150 mA flux, i.e. ≈10–11 lm, and the board drives **25 mA**, giving ≈8.7–9.5 lm.
- The RGB entries use **Kingbright KAAF-5050** data (R and G 4.4 lm, B 1.3 lm). The fitted part is the Würth 150141M173100: from its Iv–IF graph at 25 mA, Φ ≈ π·Iv gives R ≈ 1.07, G ≈ 2.9, B ≈ 0.71 lm.
- `adv_calc/modes_check.py` results (claimed → as built):

| Mode | Flux | Chromaticity xy |
|---|---|---|
| Warm 2700 | 48 → 35 lm | unchanged |
| Neutral 4000 (after cap) | 89 → 57 lm | unchanged |
| Night red | 8.8 → **2.1 lm** | unchanged |
| Candle 1900 | 19.7 → 9.5 lm | (0.539, 0.410) → **(0.438, 0.479)**: yellow-green, far off the Planckian locus |
| Night orange | — | (0.643, 0.326) → (0.584, 0.353) |

- The white modes still land on the locus, because their G correction is small.
- R20 "whites on the Planckian locus" holds; Candle does not.
- Regenerate `gen_modes.py` with the Würth data at 25 mA. VERIFY against the received bins.

**N-3 The optics model does not match the as-designed geometry.**

| Parameter | `sphere_illum.py` | Design |
|---|---|---|
| Inner radius R | 23.6 mm | CAD smooth inner 22.4 mm; real relief surface 22.4–24.1 mm, because the relief is on the inside (B11) |
| Opening half-angle | 25° and 30° | 33.3° |
| LED layout | 1 centre LED + 8 on a 6.5 mm ring | 8 whites at r = **8.0** mm (`RING_R`) plus 2 RGB at ±3 mm (`moonlib.LED_RING_R` = 6.5 is inconsistent) |
| Skirt shading | Not modelled | 2.5 mm skirt at r = 12 mm, 4 mm from the LEDs |

- PLAN's "max/min 1.001 at 33°" cannot be reproduced from the script's `__main__`.
- The visual result is dominated by the designed 3–5× transmission variation of the lithophane, so ±5 % illuminance is not critical. But the claim should be re-run on the real geometry or worded as "approximately uniform".

**N-4 It is a dim reading light.**
- At the cap, the 4000 K mode emits ≈57 lm. With an escape fraction of ≈0.5–0.7 (τ 0.35, ρ 0.55 assumed), about 30–40 lm leaves the moon, roughly isotropically: I ≈ 2.5–3 cd.
- That gives ≈40–50 lux at 25 cm and ≈110–140 lux at 15 cm. Reading tasks are usually lit at 300–500 lux.
- After M-2 derating, expect 50–70 % of these figures.
- This is a requirements risk for R1, not a safety issue. Measure lux at the page.

**N-5 Würth RGB derating.**
- The curve (datasheet p4) is flat at 30 mA to 50 °C ambient, then linear to 10 mA at 85 °C. So **25 mA is allowed only up to 58.8 °C**.
- The firmware curve keeps the RGB inside this in normal operation: 59 % at 58.8 °C, 30 % at 65 °C.
- A latched fault (M-1) at 60–75 °C exceeds it. Above 85 °C the part is outside its operating range.

**N-6 BOD versus clock: no issue.** 10 MHz with BODLEVEL2 (2.4–2.9 V) is covered by note 2 of DS40002205A Table 36-3 ("operation ensured down to VBOD with BODLEVEL2").

**N-7 Charge parameters are fine.**
- VREG is 4.20 V (4.168–4.232 V) and IREG is 417 mA, 0.35 C, within the Adafruit/PKCell 0.5 C limit. Termination is 7.5 %.
- Pimoroni publishes a "4.2 V charge cut-off" for its PCM. If that is the real overcharge threshold (DW01 parts are normally 4.25–4.30 V), a 4.232 V charger may nuisance-trip the PCM at end of charge. VERIFY with the cell's datasheet.

**N-8 Load-sharing works, with caveats.**
- On USB, D3 feeds VSYS_RAW at VBUS − 0.8 V, Q1's gate is at VBUS, so Q1 is off. The charger therefore sees only the cell and terminates. **Correct.**
- Caveat: if VBUS at the jack falls below ≈4.5 V (long or weak cable), Q1's body diode starts sharing the load from BAT. Termination may then never happen, leaving the cell floating at 4.2 V with no timer. This ages the cell but is not a hazard.
- Total USB draw is ≈650 mA: 417 mA charge, 166 mA LEDs, 15–29 mA TLC, 3 mA LED indicator. That is above the 500 mA USB 2.0 default, so strict laptop ports may cut out.

**N-9 Child safety and flammability.**
- The moon is twist-off by hand and exposes the LED board (bright point sources, and a hot board in a fault).
- The 7 mm button caps and the 26 mm board are small parts. The LiPo is behind screws, which is good.
- Label "not a toy, 14+". Consider a detent or set-screw on the bayonet.
- PLA and PETG are UL94 HB class. The worst credible temperatures (≈125 °C board, ≈4 W in D3 in M-6) are far below auto-ignition. The real risks are softening, a falling hot head, and the LiPo (B-2, B-3, M-4, M-6).

**N-10 J3 carries VSYS (up to ≈4.45–4.85 V on USB) on a Qwiic pinout.** This is already flagged in the comments. Also mark it on the silk, and use a non-Qwiic colour cable so nobody plugs in a 3.3 V Qwiic sensor.

**N-11 TLC59116 I_CC dominates low-level runtime.** At night-light levels (≈3–20 mA of LED current), the driver's quiescent current, specified up to 29 mA at 5.5 V, is most of the load. Measure the real I_CC at 3.7 V; the PLAN already notes 25–37 mA. Q4 (M-1) lets the firmware unpower the board whenever all channels are at zero.

**N-12 Things that held up (checked, no finding)**
- The slide switch carries only gate current through R7 (PCM12 rating 0.3 A at 6 V). The R6/C5/R7 RC (~1 ms) tames contact bounce.
- CC1 and CC2 each have their own 5.1 kΩ.
- D1, D3 and all PFET orientations match the netlist and datasheets (Q_PMOS_GSD = DMG2305UX G1 S2 D3).
- The TLC59116 powers up with LEDOUT = 0 (dark) and RESET is tied high. Its address pins and the LM75B's are tied.
- The firmware disables All-Call. Wire has bus timeouts (2.6.11, `TWI_TIMEOUT_ENABLE`).
- EEPROM uses magic, version, range and CRC-8 checks, and is written only on a 2 s hold. A power-cut mid-write falls back to defaults.
- Stuck buttons only change level or mode, or re-save once.
- The thermal-sensor failsafe (30 % after 3 s) is sound **when the bus works**: the board settles at ≈38–45 °C.
- The firmware cap and mode recipes can never ask for more than 166 mA actual, apart from the m-4 glitch.

---

## 5. Recommended change list, by priority and cost

| # | Change | Fixes | Cost |
|---|---|---|---|
| 1 | Firmware: un-shutdown and verify the LM75B in `setup()` (or never shut it down); add a staleness check | B-1 | 0 |
| 2 | Pack CAD: no screw heads or THT on the PCB's back face, or add a separator plate with pockets; J4 never fitted | B-2 | 0 / ~2 mm thickness |
| 3 | Pack CAD: J2 plug pocket and defined battery-lead channel (or re-orient J2) | B-3 | 0 |
| 4 | LED board: LM75B OS → TLC /RESET with 10 kΩ pull-up; firmware sets Tos/Thyst and reads back | M-1 | 1 resistor |
| 5 | Main board: Q4 DMG2305UX high-side moon-feed switch on a spare pin (100 kΩ pull-up, gate RC); pull-ups on the switched rail | M-1, M-3, N-11 | ~£0.35 |
| 6 | Fuse-locked WDT; bus recovery; register read-back | M-1, m-5 | 0 |
| 7 | Moon clamp: PETG ring clamps the board, PLA kept clear; or lower thresholds to 40/48/55 °C and accept lower sustained output; measure | M-2 | 0 / redesign |
| 8 | VBUS PTC (MF-MSMF075-2 class) ahead of the TVS; OVP switch (NCP361-class) if budget allows | M-5, M-6 | £0.2–0.6 |
| 9 | R3 2.4 kΩ → 4.7 kΩ (≈213 mA); insulating pad under the charger; consider BQ21040 + NTC | M-4 | 0 / ~£1 |
| 10 | PTFE wire or sleeve in the neck, thread-end bushings, strain-relief holes on the LED board, cable anchor in the pack | M-7 | ~£1 |
| 11 | `I_CHANNEL_MA` = 25.0 (generated); regenerate modes with Würth data; fix the IREF/PWM order | m-3, m-4, N-2 | 0 |
| 12 | R5 100 kΩ → 10 kΩ | m-2 | 0 |
| 13 | Insulating disc over the nut; 100 Ω series on SDA/SCL; ESD diodes at J3 | m-6 | ~£0.2 |
| 14 | User sheet: switch off after use; charge between 5 and 40 °C; meter the pack polarity before first plug-in; do not recharge a pack that has sat flat (< 2.5 V) | M-3, M-4, m-1 | 0 |

**Measurements to add to `docs/verification/VERIFY.md`:**
- Board and PLA-skirt temperature at the cap on USB, at 25 °C and 35 °C ambient, with and without derating. Also with the firmware halted (simulating M-1).
- Pouch temperature under U1 during the first 30 min of a charge from 3.0 V.
- TLC59116 I_CC at 3.7 V with all outputs off.
- Remaining capacity and time from "empty" to the PCM cut-off, with the switch on.
- Neck bend torque.
- JST-SH retention after 500 neck bends.
- Lux at the page at 20 cm and 30 cm.
