# main-board v0.1 - fabrication notes (paste into the fab's order form)

- 2 layers, FR4 TG130-150, **1.6 mm**, 1 oz outer copper, 35.0 x 62.0 mm, rounded corners (r 2 mm)
- Surface finish: HASL lead-free (ENIG optional), solder mask green, silkscreen white
- DRC: 0 errors. Two silk warnings are intended: the SW1 slide-switch outline crosses the right board edge because
  its knob overhangs the edge by design (the fab clips silk at the edge).
- Min track / space 0.20 / 0.20 mm; min via 0.6 / 0.3 mm (drill); min hole 0.3 mm; no blind/buried vias, no castellations
- Plated slots: 4 x 0.6 x 1.2 mm (USB-C shell pegs), in the PTH drill file. NPTH: 2 x 0.9 mm (slide-switch pegs),
  2 x 2.2 mm (M2 mounting holes). PTH: J4 header (DNP). Internal routed cut-out 6.4 x 5.0 mm, r 0.4 (battery-lead
  slot, on Edge.Cuts)
- Quantity 5. Stencil: top side only, frameless, 0.12 mm
- Assembly (optional): all parts on TOP; BOM/CPL files: bom_pcbway.csv + cpl_pcbway.csv or bom_jlcpcb.csv + cpl_jlcpcb.csv.
  J4 (programming header) and TP1-TP7 (test pads) are not populated.
