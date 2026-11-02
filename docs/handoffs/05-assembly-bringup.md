# Handoff 05: assembly and bring-up

**For:** Matt at the bench, with Claude Code in VS Code following along. Claude reads the debug log, checks values
against `docs/verification/VERIFY.md` and records them there. Allow about 3 h for the first lamp.

**You need:**
- Tools: a fine-tip iron, a hot plate or hot air (for the stencilled side), flux, IPA, tweezers, a 10× loupe, a
  multimeter with diode test, and a bench supply with a current limit (or a spare charged cell plus the meter).
- Assembly drawings: `fab/<board>/v0.1/assembly_top.pdf` / `assembly_bottom.pdf`.
- Off-board items, from `bom/other_purchases.csv`: Kapton tape, PTFE sleeve, heat-shrink, CA gel, and neutral-cure
  silicone (or E6000) for strain relief.

## 1. Main board (all parts on top)
1. Inspect the bare board: no shorts between VBUS / BAT_RAW / VSYS / GND. Meter the TPs to TP4 GND.
2. Stencil and paste, then place the parts per `assembly_top.pdf`: passives, SOT-23s (Q1–Q4, check the orientation
   dots), U1 MCP73831, U2 ATtiny3216, D1/D3 (cathode bar to the silk bar), and the red 0603 D2. Reflow.
3. The mechanical parts can go through the same reflow if the stencil printed their pads, or be fitted by iron:
   J1 USB-C (also solder its shell pins through the holes by iron), SW1 PCM12, SW2–4 tact switches, J2 PH and J3 SH.
   **Do not fit J4**: hold a header in the holes when programming. A soldered header would point at the pouch
   (round1 B-2).
4. Clean off the flux. Under the loupe, check U2's pins and the USB-C pads for bridges.
5. Run VERIFY **E1–E4** now (bench supply on J2, no cell, no LED board). E2 finds which knob direction is ON: mark it.
6. Flash the firmware: handoff 04, steps 1–5. With no LED board fitted, the lamp just retries quietly. The debug
   log shows `T=-99` and then the 30 % fail-safe cap. That is expected.

## 2. LED board (bottom first, then top)
1. **Bottom side** (stencil 2): U1 TLC59116 (TSSOP-28, pin 1 dot), U2 LM75BDP (TSSOP-8), R1 750 Ω, R2 10 k,
   C1–C3. Reflow, then check every TSSOP pin for bridges under the loupe.
2. **Top side**: 8 × white 2835 (4 × 2700 K, 4 × 5000 K at the positions on `assembly_top.pdf`; cathode mark per
   silk) and 2 × Würth RGB (pin 1 = common anode, corner mark). Use hot air or the iron at ≤ 260 °C, ≤ 10 s per
   joint: the LEDs are heat-sensitive. The bottom-side parts must not reflow again, so don't put this side on the
   hot plate.
3. Diode-test each LED: + probe on pad V (VLED, all anodes), − probe on its TLC output pin. Each one should glow
   faintly in the right colour; a dark one is reversed or open. Green and blue need about 2.6 V to glow, so a meter
   whose diode test gives less can only check them at first light.

## 3. Cable and neck (round1 M-7: abrasion and strain relief)
Qwiic cable colours: **black = GND, red = VLED, blue = SDA, yellow = SCL**. The LED board pads are labelled
**G V D C** on its bottom silk.
1. Deburr the inside of both gooseneck ends with a needle file. Self-tap the gooseneck's lower end into
   `pack_front`'s 9.3 mm socket by hand, before any cable is fitted, so nothing twists. A drop of CA gel on the
   thread is optional. **No anaerobic thread-locker**: it crazes PETG (round1 m-7).
2. Cut the Qwiic cable to about 200 mm, keeping the JST-SH end. Slide the PTFE sleeve over the 4 wires. Feed the
   bare end up through the gooseneck from the pack side. Put 15 mm of heat-shrink over the wires where they leave
   each threaded end.
3. Thread the wires through the M10×1 nut. Push the gooseneck's top end up through the `moon_base` floor, and spin
   the **nut** (not the gooseneck) down into the hex socket. Wires out through the cable notch.
4. Solder G / V / D / C on the LED board. Cover the joints and 5 mm of wire with neutral-cure silicone and let it
   cure. This is the strain relief.
5. Lay the LED board on the base ledge (LEDs up), then the PETG `moon_ring` on its edge band. Fit the moon: lugs
   into the entry slots, then turn 30° to lock. To remove the moon, **hold the base cup**, so the turn doesn't
   unscrew the base from the neck.

## 4. Pack
1. Put Kapton tape over the top face of the pouch, and a patch on the PCB back under U1, D3 and Q1–Q3.
2. **VERIFY E1 again on the real cell: + must be on J2 pin 1.** Plug J2, with the lead running through the slot.
3. Fit the button caps into the front shell. Plug the JST-SH into J3. Anchor the cable to the PCB edge with a dab
   of silicone, about 10 mm before the connector, so a pull on the neck never reaches the JST-SH (it has no latch).
   Screw the PCB onto the bosses with 2 × M2×6.
4. Battery into the bay. Hook the back-plate tabs into the slots, then fit 2 × M2×12 through the clip root and the
   plate into the front shell.

## 5. First light and checks
1. Switch ON with no USB. The lamp should fade into Soft white 3000 K at level 10. Run through the modes, UP/DOWN
   and hold-to-save (two dips).
2. Debug build (handoff 04 §5): run VERIFY **F2–F5** and **E7–E12**.
3. Before regular use, run at least **T3** (4000 K full for 2 h with thermocouples, or a contact thermometer on the
   moon skirt) and **T6** (the thermostat). Record the results in VERIFY.md and send them to Claude, who re-fits
   the derating if the board-to-PLA offset is not about 14 K.
4. Light and colour: VERIFY **O1–O7** as equipment allows. A phone lux app is good enough for O3.

## 6. User notes (for whoever uses the lamp)
- Charge at room temperature (the charger has no cell-temperature sensing). The red LED means charging. It flickers
  when no battery is connected, which is normal.
- The side switch is the only off. Switch off when you put the lamp down.
- After a "battery empty" fade-out, plug in USB. The lamp comes back on by itself after a few seconds.
- If the pack ever bulges, stop using it and replace the cell.
- Never power the lamp from a programmer or a USB-UART adapter.

## Done when
One lamp is assembled and every E, F and T3/T6 item has a measured value in VERIFY.md. Anything outside its pass
band is raised with Claude before the second lamp is built.
