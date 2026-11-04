# led-board v0.2 - fabrication notes (paste into the fab's order form)

- 2 layers, FR4, **1.0 mm**, 1 oz outer copper, round **18.0 mm** diameter
- Surface finish: **ENIG** (flat pads for the 2835 LEDs and the 0.4 mm pitch WQFN)
- Solder mask **WHITE** both sides (the top face is the reflector inside the moon), silkscreen black
- Min track / space **0.15 / 0.15 mm**; vias 0.6 / 0.3 mm (drill), min hole 0.3 mm; no blind/buried vias;
  vias tented both sides
- Quantity 5. Stencils: top 0.12 mm (LEDs) and bottom **0.10 mm** (LP5012 WQFN-20, 0.4 mm pitch); frameless
- Small round board: please leave no breakaway-tab nubs on the edge (it sits in an 18.4 mm pocket), or we sand them
- Silk: "W" = 2700 K and "C" = 5000 K beside each white LED; RGB D9: the package's polarity mark (pin 3, red
  cathode) goes on the silk chamfer; cable pads G V D C on the bottom
- Assembly (optional): TOP: D1-D9 and R2 (0402); BOTTOM: U1 LP5012 (WQFN-20), U2 MCP9800 (SOT-23-5), R1, C1-C4.
  J1 = 4 solder pads for the cable (not a component). Two-sided assembly costs extra; or assemble the bottom
  only and hand-fit the top.
