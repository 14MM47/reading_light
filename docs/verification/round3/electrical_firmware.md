# Round 3: electrical + firmware review (LED board v0.2, LP5012 / MCP9800 layer)

Independent reviewer, 2026-11-04. Scope: `hardware/led-board/design.py` and its outputs (`led-board.kicad_pcb`,
`fab/led-board/v0.2/*`, `reports/{erc,drc,route}.json`), the project symbol/footprints, `firmware/` (main.cpp,
lib/core, config.h, board_map.h, modes_table.h, tests), `tests/test_consistency.py`, and the docs listed in the brief.
Main board v0.1 only at the interface: Q4/VLED, R8/R9 3.3 k on VLED, J3.

Sources: TI SLVSEH2B (LP5009/LP5012, rev. Aug 2020), Microchip DS21909D (MCP980x), Würth 150141M173100 rev 002.011
(p2 table, p3 VF–IF curve, p4 derating curve), Bridgelux DS312 (via KEYSPECS §3). Method:
- Read every file in scope.
- Loaded the board through `pcbnew` (read-only) and dumped pads, tracks, vias and zone fills.
- Measured copper necks at the track-to-pad joints. I eroded the shapely union of each pad and track.
- Ran a shortest-path search through the GND copper on B.Cu (fill + tracks + pads, 25 µm grid).
- Read the B_Cu Gerber at the IREF joint, and the mask Gerbers for via tenting.
- Ran `pio test -e native`: 29/29 pass.
- Checked megaTinyCore 2.6.11's Wire buffer: 32 bytes when RAMSIZE < 4096, so the 17-byte burst fits.

No repo file was edited except this report. Some docs changed on disk during the review (C2 at about 6 µF, E17 now
uses a `bench_tstat_low` env). The findings below are against the current text.

## Summary

**0 BLOCKER, 0 MAJOR, 5 MINOR, 8 NOTE.** The circuit is correct against both datasheets:
- the LP5012 and MCP9800 pinouts, addresses 0x14/0x48, RIREF 25.0 mA, EN/ALERT wiring and VCAP;
- every LED cathode on the output that `board_map.h` names;
- all register values (0x40, 0x1C, 0x00, 07h–16h, 17h=FFh; CONFIG 0x68, TSET/THYST encoding, 12-bit decode);
- the brightness/colour quantisation and the write-ordering argument.

Nothing here would damage hardware.

The MINOR items:
- **R3-E1.** The router connected IREF to the very corner of U1 pin 20. The joint is a 0.106 mm copper neck, below
  the board's 0.15 mm rule.
- **R3-E2.** The VCAP capacitor and RIREF return to the LP5012's exposed pad (its only GND) through 22–26 mm of
  copper. The NE region is fenced in by the SDA/SCL/EN/IREF bundle.
- **R3-E3.** Green/blue headroom is stated only for typical parts. A maximum-V_F die needs about 4.05–4.15 V.
- **R3-F1.** SLVSEH2B's OUTx_COLOR field tables are inverted relative to the rest of the datasheet. `lp_init()` sets
  Chip_EN before it zeroes the outputs.
- **R3-F2.** The output registers are written only on change and never read back. A corrupted transfer persists.

## Findings

| ID | Sev. | Finding (evidence) | Recommended fix |
|---|---|---|---|
| R3-E1 | MINOR | **IREF joint at U1 pin 20 is a 0.106 mm neck.** The routed IREF track starts exactly on the pad's outer corner: B_Cu Gerber `X50900000Y-48250000D02` → `Y-46100000D01` (aperture C0.15). Pad 20 is RoundRect 0.2 × 0.7, r 0.05 (`ADD16`), centred at X50.8 Y-48.6, so the track end sits 21 µm outside the rounded corner. The largest disc that passes from pad to track is 0.106 mm across; the same track on the pad centreline gives 0.149. The R1 end is also a corner attach (0.129 mm at (1.0, −4.1) on R1 pad 1). These are the only joints on the board below 0.15 mm; every fixed (design.py) track starts at a pad centre. DRC cannot see it: no `connection_width` constraint is set. An etched-open IREF floats the pin and the outputs go to ~0 (SLVSEH2B §8.3.3, p17). An intermittent IREF is worse. | Make IREF fixed copper in design.py from the pin-20 centre (0.8, −1.4) north to R1 pad 1's centre, as `fanin_tracks()` does, or make kigen end pad entries on the pad centreline. Add `(rule "neck" (constraint connection_width (min 0.15mm)))` to the board's .kicad_dru so DRC catches it. |
| R3-E2 | MINOR | **VCAP, VCC and RIREF are electrically far from the LP5012's ground.** GND is bottom-only and the EP has no vias. Its only exits are the two 0.2 mm links to pins 14/15 and a 0.3 × 2.35 mm track north from pin 15 (design.py:361-365). The I²C/EN bundle (pins 17–19, then arcs r 6.4–7.45) and the IREF track wall off the NE region where C4 and R1 sit, so their GND pads reach the EP only around the board. Shortest B.Cu GND copper path to the EP centre: **C4.2 (VCAP cap) 22.2 mm** (straight line 4.4); **R1.2 (RIREF) 25.6 mm** (4.9); C1.2 5.4 mm. C1's VCC side is pin 16 → via → 7.5 mm of top VLED copper → via. TI §11.1 (p37) says: "Place the CVCAP, CVCC and RIREF as close to the device as possible", with the GND plane of Fig. 11-2. §9.2.2 (p36) says the VCAP cap "must" be 1 µF "as close … as possible". The docs claim otherwise: led-board-v0.2.md:47 ("VCC 1 µF (C1) at the pin") and design.py:157 ("at pin 1"). DC effect is small: LED return current through the shared EP links and the pin-15 track gives ~1–1.5 mV at R1 (0.2 % of V_IREF). The VCAP loop is ~20–25 nH, though, so the cap stops working above ~1 MHz for the LDO and the 15 MHz logic. | Better now than after the order: give C4/R1 a short GND. Option (a): a GND jumper across the north gap on the top face (one via beside C4/R1's GND pads, one in the NW pour beside the pin-15 track, ~2–3 mm of top track; the VLED pour flows round it). Option (b): turn C4/R1 so their GND ends land in the NW pour next to the pin-15 track. If left as is: correct the two "at the pin" claims, and add a bench item that scopes VCAP (AC-coupled) and one channel's current at 4000 K full. Pass: no ripple bursts and E8 current steady. |
| R3-E3 | MINOR | **G/B headroom: only the typical case is stated.** Würth p2 gives V_F max 3.6 V at 20 mA. The p3 curve adds ~+0.09 V at 25 mA, so ~3.7 V. V_SAT 0.25/0.35 V is specified at **20 mA** (SLVSEH2B §7.5, p8); at 25 mA it is unspecified and likely higher, ~0.31/0.44 V for a resistive knee. A maximum-V_F G or B die therefore needs VLED ≈ 4.05–4.15 V. That is above VLED on USB (VSYS 3.9–4.1 V, electronics.md §1) and above a 4.2 V cell after the ~80 mV path drop at 4000 K full. Such a die is never fully regulated. The docs give only the typical knee: electronics.md:68-72 ("regulated above V_LED ≈ 3.65 V typical"), led-board-v0.2.md:45, and E9's pass line (VERIFY.md:35, "VF 3.3 V + VSAT 0.35 V"). Effect: Green/Blue modes are dimmer, and the G/B share of 3000/4000/6500 K drops, so Duv goes negative (pink) over most of the charge, not just the last 30 %. Whites (max ~2.92 V + 0.44) and red are fine down to about the 3.45 V low-battery threshold. | State the worst case in electronics.md §2 and led-board-v0.2 §2/§7. Make E9 a measured-V_F test: measure the received dies' V_F at 25 mA first, then pass if the peak holds down to V_F + 0.35–0.45 V. Keep R1 3.65 kΩ (20 mA everywhere) as the remedy if the received dies sit high, or buy a known V_F bin. |
| R3-E4 | NOTE | **LP5012 thermal path.** The EP is copper-isolated from the pour: two 0.2 × 0.2 mm links (~37 K/W), then a 0.3 × 2.35 mm track (~570 K/W). TI §11.1 asks for "as many thermal vias as possible" under the pad, and there are none; the top face above U1 is D9 and the VLED pour. Dissipation: ≈ 0.25 W at 4000 K full, VLED 4.12 V [(4.12−2.75) V × 165 mA + (4.12−3.3) × 12 mA + 5 mA × 4.1 V]. The brief's worst case (11 × 25 mA at 4.2 V, not reachable with the 200 mA cap) is ≈ 0.41 W. Heat leaves through the 12 cathode legs and the FR4; I estimate 45–70 K/W junction to local copper, including RθJC(bot) 12.9 (p7). That gives ΔTj ≈ 12–30 K, so Tj ≲ 90 °C at the 60 °C trip: inside TJ 125 °C and far from TSD 160 °C (§8.3.5.1, p17). The 2835 cathode (thermal) pads are also isolated islands, inherent to low-side sinking. U1, D9 and the inner cathodes are the hot spot, ~5.7 mm from U2, so the sensor under-reads them. | Accept. T3 already bounds TC2 (LP5012) ≤ 80 °C. Put TC2 directly on U1 (centre of the bottom) and record TC2 − T= (sensor) as the real offset for T2's re-fit. |
| R3-E5 | NOTE | **LP5012 supply current.** §7.5 (p8) gives 4 typ / 6 max mA "with 10-mA LED current per OUTx". §8.4 (p18) says "NORMAL … ICC is 10 mA (typical)". KEYSPECS:403 records both, but electronics.md:74, :99 and :105 use 4–6 mA only, so red night ~150 h could be ~100 h. | Quote "4–6 mA (§7.5); §8.4 says 10 mA typ", and leave the runtime to E7's measurement. |
| R3-E6 | NOTE | **Würth derating curve (p4) is not in KEYSPECS:** 30 mA flat to 50 °C ambient, then linear to 10 mA at 85 °C, so 25.0 mA at 58.8 °C and 24.3 mA at 60 °C. The firmware derating (×0.5 at 50 °C, ×0.3 at 52 °C) keeps the average far inside it. Only a hung firmware holding G or B at 100 % between 58 and 60 °C (the 60 °C trip) is 3–8 % over, a double fault. | Add the curve to KEYSPECS §2 and electronics.md §2. No design change. |
| R3-F1 | MINOR | **OUTx_COLOR polarity: datasheet contradiction, and init order.** SLVSEH2B Tables 8-17…8-28 (OUT0–OUT11_COLOR, p29-33) say "FFh = 0 %, 00h = 100 %". Table 8-10…8-12 (BANK_x_COLOR, p27) say FFh = 100 %. The reset default 00h, the "LEDs off" power-save text (§8.3.4, p17) and the firmware (lightcore.h:79, colour 0 = off) assume FFh = 100 %. That is almost certainly the right reading, but KEYSPECS:412 does not record the conflict. `lp_init()` writes Chip_EN first (main.cpp:50) and zeroes 07h–16h three transactions later (main.cpp:54). LEDx_BRIGHTNESS resets to FFh, so if the OUTx table were literal, every init (boot, re-init, thermostat release) would start with ~1–2 ms of all 11 channels at 25 mA. | Write LED_CONFIG0, CONFIG1 and the 16 zero bytes **while still in STANDBY**, then Chip_EN last. Registers are writable in STANDBY (§8.4, p18). Brightness 00h = 0 % (Table 8-13, p28) is unambiguous, so the order is safe whichever way the colour table is right. Record the contradiction in KEYSPECS. Add to E8: colour 0 → 0 mA and colour 255 → 25 mA. |
| R3-F2 | MINOR | **Output registers are never refreshed or read back.** `lp_output()` returns early when the computed registers equal `last_regs` (main.cpp:69). The 1 s check reads only CONFIG0 (main.cpp:333-334). CONFIG1 is verified only in `lp_init()` (main.cpp:56). The bus is a 200 mm cable in a metal neck, next to the PWM return current, and I²C has no CRC. A single bit error in the register-address byte changes the burst start: `0x07→0x03` shifts colour bytes into LED1–3_BRIGHTNESS, up to 255/b brighter; at level 0 (b = 2) that is ~65×, on OUT3–OUT11, with the mix scrambled. A data-bit error mis-sets one register. Either state persists until the drive next changes. With a steady night light that can be hours, because derating rewrites only above 45 °C. | In the 1 s check, read 00h–01h and re-init if CONFIG0 ≠ 0x40 or CONFIG1 ≠ 0x1C. Read back 07h–16h (16-byte auto-increment read, §8.5.1.6–7, p21-22; ~2 ms/s at 100 kHz) and set `lp_ok = false` on any mismatch with `last_regs`. |
| R3-F3 | NOTE | **Thermostat-hold path.** While ALERT holds EN low, the retry loop rewrites THYST/TSET/CONFIG every 500 ms (main.cpp:315). DS21909D does not say whether a CONFIG write affects the comparator output or the fault-queue count (p18, p24-25). If it resets them, the 52 °C hysteresis is lost and EN can chatter. Separately, `lp_fails` keeps counting during the exemption (main.cpp:319-320), so the first reading below THYST power-cycles the board at once. ALERT may not have released by then: fault queue 2 needs 2 × 240–600 ms conversions. That is harmless, but it is not the intended "natural" release. Also, E17's "within ~0.5 s" is typical; the maximum is 1.2 s. | In the retry path, call `ts_setup()` only if `!ts_config_intact()`. Hold `lp_fails` at 0 while the exemption applies. Watch for EN chatter in T6 (scope EN). |
| R3-F4 | NOTE | **0 °C after an unplanned LED-board POR.** `ts_valid_after` is re-armed only in `led_board_on()` (main.cpp:205). After a cable or VLED glitch, the MCP9800 restarts at 9-bit with TA = 0000h = 0 °C until its first conversion (≤ 75 ms; Table 5-4, p25; p3). The 1 s read can catch that 0 °C, and it passes the −20…100 °C check (lightcore.h:27-28, lightcore.cpp:167). It sets `t_cap_target` 1.0 for one second, and `last_temp_c = 0` lifts the thermostat exemption (main.cpp:320). | Set `ts_valid_after = millis() + 700` wherever `lp_ok` drops on a Chip_EN or NACK detection (main.cpp:334, :330). |
| R3-F5 | NOTE | **Warm restart.** `core_init()` sets `t_cap = 1.0` (lightcore.cpp:106). The first reading comes at ≥ 1 s, and the cap then slews at 10 %/s (lightcore.cpp:223-231). After a WDT reset at 55 °C the head runs at the 110 mA cap for ~8 s before reaching the ×0.17 derate. Not hazardous (the thermostat backs it up), but avoidable. | On the first valid reading after init, set `t_cap = t_cap_target` (no slew). |
| R3-F6 | NOTE | **Frozen-sensor false positive.** "Trusted" needs the reading to change within 5 min while > 50 mA flows (lightcore.cpp:184-190). At thermal equilibrium, a quiet 12-bit MCP9800 can sit on one 0.0625 °C code for 5 min. 4000 K full would then fade 177.5 → 110 mA. The next code change restores it, so the lamp could slowly "breathe". T5b tests the true-positive case only. | Log `T=` for 15 min at steady state in T3. If codes stall, keep trust once the reading has risen ≥ 1 °C since `load_since`, and revoke it only on NACK, an out-of-range reading, or no rise in the first 5 min of load (still catches a sensor stuck from the start, as in T5b). |
| R3-F7 | NOTE | **Steps after re-init.** After any re-init (thermostat release, cable glitch), `lp_init()` zeroes the outputs and the next `lp_output()` writes the current drive as one step, not a 160 ms fade. | Optional: call `retarget()` from 0 when `lp_ok` goes true. |

## Checked and found correct

- **LP5012 pins** (SLVSEH2B Pin Functions, p6), symbol (`reading_light:LP5012RUK`), PCB pads and design.py:149-152 all
  agree: 1 VCAP, 2–13 OUT0–11, 14/15 ADDR0/1 → GND, 16 VCC = VLED, 17 SDA, 18 SCL, 19 EN, 20 IREF, pad 21 (EP) GND
  with `zone_connect 2`. The address is 0010100 = **0x14** (Table 8-2, p21) and matches config.h:9. Unused OUT6
  (pin 8) floats, which p6 allows, and the firmware writes it 0.
- **R1 2.94 kΩ** gives 105 × 0.7 / 2940 = **25.0 mA** (Eq. 1, p17). That is under I_MAX 25.5 mA with
  Max_Current_Option 0 (p8, p17), and under the Würth 30 mA at ≤ 50 °C. `tests/test_consistency.py` and
  `test_channel_current_matches_riref_2k94` both tie it to I_CHANNEL_MA.
- **Ratings and decoupling.** VLED ≤ 4.2 V is inside the 5.5 V recommended / 6 V absolute maximum on VCC, OUTx and EN
  (p7). The 6.4–7.5 V USB fault is documented as accepted (electronics.md §1). VCAP has 1 µF 25 V X5R 0402, about
  0.9 µF at ~1.8 V; its absolute maximum is 2 V. VCC has 1 µF, and there is 10 µF bulk.
- **MCP9800A0** (DS21909D p9, Tables 3-1/3-2): SOT-23-5 pins 1 VDD, 2 GND, 3 ALERT, 4 SCLK, 5 SDA match the KiCad
  symbol and the design. The address is 1001000 = **0x48**.
- **EN and ALERT levels.**
  - EN V_IH 1.4 V (p9) is met through R2 2.4 kΩ to VLED (leakage ≤ 2 µA).
  - ALERT sinks ≤ 1.75 mA. V_OL ≤ 0.4 V is specified at 3 mA (p3), so at 1.75 mA it sits below EN's V_IL 0.4 V.
  - The U2–EP ground offset is ~1 mV.
  - The SCL→EN coupling along the r 6.4/7.0 arcs is ~0.3–0.5 pF, which dips a 2.4 kΩ node by about 0.25 V. That
    stays far above V_IH.
- **Cold power-up.** POR is comparator, active-low, TSET 80 / THYST 75 °C, TA = 0 (Table 5-4, p25), so ALERT is
  released and cannot hold EN at a cold start. There is no LP5012/MCP9800 init race: `ts_setup()` runs before
  `lp_init()`, and ALERT needs ≥ 1–2 conversions to assert. tEN_H (500 µs, p9) is covered by the 10 ms wait
  (main.cpp:199) after Q4's ~2 ms ramp.
- **LP5012 register values** (Tables 8-4, 8-6, 8-7, p23-25):
  - Chip_EN = bit 6 (0x40).
  - CONFIG1 0x1C = log off, power-save on, auto-increment on, dither on, Max_Current_Option 0, Global_Off 0.
  - LED_CONFIG0 0 (no banks).
  - LEDx_BRIGHTNESS 07h–0Ah each cover OUT3k..3k+2 (§8.3.1.2.1, p13). OUT0–11_COLOR are 0Bh–16h, one contiguous
    16-byte burst.
  - RESET 17h ← FFh (p34). Every EN rise, UVLO or RESET puts the device in INITIALIZATION, and all registers reset
    (§8.4, p18). The 1 s Chip_EN read-back catches this; the device is dark (STANDBY) until then.
  - Power-save exits on any I²C command (§8.3.4, p17), so the read-back never misfires.
- **MCP9800 register values** (Register 5-3, p18; Table 5-1, p15):
  - CONFIG 0x68 = 12-bit, fault queue 2, active-low, comparator, continuous.
  - TSET/THYST are `(°C·2)<<7`: 60 → 3C00h and 52 → 3400h, matching the datasheet's 90 °C = 5A00h example. They fit
    a 16-bit int on AVR.
  - The read-back compares CONFIG, the TSET MSB and LSB bit 7, which is correct.
  - TA decode `(int16)raw >> 4 × 0.0625` is right at 9 to 12 bits.
  - The 700 ms first-read wait leaves ~95 ms of margin over CONFIG-write + 600 ms.
- **Recovery.** The power-cycle bleed works:
  - Wire clears PORTB OUT bits 0/1 (twi_pins.c:145), so driven SDA/SCL really go low.
  - With ~6 µF and 1.65 kΩ (τ ≈ 10 ms), 200 ms takes VLED well below UVLO 2.0 V and the MCP9800's 1.7 V POR.
  - The exemption keys on the MCP9800 reading against THYST, as intended. A dead sensor falls back to power-cycling.
- **Channel map.**
  - From the PCB pads: OUT0 K_D2(CW), 1 K_D1(WW), 2 B, 3 K_D8(CW), 4 K_D7(WW), 5 G, 6 spare, 7 R, 8 K_D6(CW),
    9 K_D5(WW), 10 K_D4(CW), 11 K_D3(WW).
  - That is `{1,0,4,1,0,3,-1,2,1,0,1,0}`, which equals board_map.h. DRC parity is 0.
  - The 2835 large pad is K (Bridgelux Fig. 16). D9 pads are 1 A, 2 B, 3 R, 4 G (Würth p1, Device:LED_ABRG).
  - `GROUP_LEDS {4,4,1,1,1}` is checked by the consistency test.
- **Quantisation.**
  - `lp_brightness()` returns 1–255 and never 0. `lp_colour()` returns 0 for b = 0 or d ≤ 0, so there is no divide
    by zero.
  - The strongest colour is bounded at ≤ 255.0x before the clamp, so no colour exceeds 255. That bound also keeps
    the 16-bit-int cast on AVR safe (v ≤ 256).
  - Rounding is +½ LSB at most, so no output is brighter than requested beyond half a step.
  - The hysteresis band [b/2, b] keeps the strongest colour at ≥ 127.
  - Write ordering holds per output in all three cases. b↓ or equal, brightness-first: intermediate (b_new, C_old)
    ≤ old. b↑, colours-first: (b_old, C_new) < new. A partial failure re-inits to zero.
  - Level 0 is b = 2 × colour 130, as the docs say.
- **Thermal logic.**
  - The caps count only LED current; the LP5012's ~21 mW replaces the TLC's ~0.1 W, so the margin improves.
  - TSET 60 sits above the 58 °C 5 % floor on the same sensor, so the ±1 °C accuracy (p3) does not reorder them.
  - Fault-queue-2 latency is 0.5–1.2 s.
- **Copper and fab.**
  - No 180 mA path uses 0.15 mm copper. The LED return goes EP → 2 × 0.2 mm links → 0.3 mm track (~4.5 mΩ,
    ~0.9 mV) → pour → J1; VLED goes via J1 → 0.3 mm + one via → top pour. 0.15 mm tracks carry ≤ 25 mA.
  - Vias are tented: `(tenting front back)`. B_Mask has 40 and F_Mask 22 openings, all pads.
  - Copper stays ≤ r 8.0 (SDA arc edge r 7.78).
  - ERC 0, DRC 0 / 0 unconnected / 0 parity. Host tests 29/29 pass.
- **Main-board interface.**
  - J3 is 1 GND, 2 VLED, 3 SDA, 4 SCL (Qwiic colours). The LED board's G V D C silk sits at the right pads.
  - Pull-ups are on VLED, with no back-feed.
  - The LP5012's V_IL 0.4 V is met with ~0.1 V of margin after the cable's GND offset, which C2 bounds.
