# led-board v0.1 - fabrication notes (paste into the fab's order form)

- 2 layers, FR4, **1.0 mm**, 1 oz outer copper, round **26.0 mm** diameter
- Surface finish: **ENIG** (flat pads for the 2835 LEDs and TSSOP-28)
- Solder mask **WHITE** both sides (the top face is the reflector inside the moon), silkscreen black
- Min track / space 0.20 / 0.15 mm (design rule; narrowest gap on the board ~0.19 mm); vias 0.6 / 0.3 mm (drill),
  min hole 0.3 mm; no blind/buried vias
- Quantity 5. Stencils: top AND bottom (frameless, 0.12 mm; both on one foil if cheaper)
- Small round board: please leave no breakaway-tab nubs on the edge (it sits in a 26.4 mm pocket), or we sand them
- Silk: "W" = 2700 K and "C" = 5000 K next to each white LED; RGB LEDs: pad 1 ("1") = common anode, the package's
  polarity mark (pin 3, red cathode) goes on the silk chamfer
- Assembly (optional): LEDs (D1-D10) on TOP; U1 TLC59116, U2 LM75BDP, R1, R2, C1-C3 on BOTTOM. J1 = 4 solder pads for the cable
  (not a component). Two-sided assembly costs extra; or assemble the bottom only and hand-fit the ten LEDs.
