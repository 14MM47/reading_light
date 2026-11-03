# Assembly routes — price comparison (you asked to "discuss price difference of all 3 options")

Quantities: 5 main boards + 5 LED boards (fabs' minimum batch), parts for **2 complete lamps** + spares (bare-board
route) or 5 + 5 populated boards (assembly routes). GBP incl. 20 % VAT, £1 ≈ US$1.30. **All figures are estimates from
published fee tables and recent user reports (2025–2026); run the fabs' instant quotes with the real Gerbers/BOMs
before ordering.** Detail and sources: `docs/research/neck-battery-pcb-pricing.md` §C.

| | Route 1: bare PCBs + stencils, Farnell parts, hand assembly | Route 2: fab turnkey assembly (fab sources parts) | Route 3: fab assembly with consigned Farnell parts |
|---|---|---|---|
| PCBs (5 + 5) | PCBWay £10–20 / JLCPCB £5–12 | panelised (both boards < 50 × 100 mm) £8–30 | as route 2 |
| Stencils | PCBWay ~£16–24 (frameless: main top, LED top + bottom) / JLCPCB ~£5–8 | included | included |
| Assembly fees | — (your time: ~1.5 h per lamp) | PCBWay ~£45–70 single-side + £70–115 double-side (LED board); **$29 1–20 pc promo if it applies** / JLCPCB: Economic main board ~£10, LED board Standard double-sided ~£55 (or Economic bottom-only ~£10 + hand-fit the top LEDs) | as route 2 |
| Parts | Farnell **~£47** for 2 lamps + spares (`bom/farnell_order.csv`, £39 ex VAT) + DigiKey UK LP5012 ~£3 (+ ~£12 shipping below its free threshold) | PCBWay £70–125 (markup 20–300 % reported) / JLCPCB £35–60 (LCSC; LP5012, MCP9800, Bridgelux, Würth are "extended" parts, ~£2.40 feeder fee each; check LCSC stock for LP5012**RUKR**, the WQFN) | Farnell £70–115 incl. the fab's overage rules (≥50 pcs per passive line, +30) |
| Shipping | DHL £15–25 (PCBWay) / £5–15 (JLCPCB post) | £15–25 (PCBWay promo may include) | + courier UK → Shenzhen **£30–70** |
| **Total (5 + 5 boards)** | **PCBWay ~£95–140, JLCPCB ~£70–100** (+ solder paste ~£10 if you have none) | **PCBWay ~£210–450 (likely ~£260), JLCPCB ~£150–250** | **~£250–500**, slowest (+1–2 weeks) |
| Lead time to boards in hand | 1–2 weeks | 2.5–4 weeks (PCBWay) / 1.5–2.5 weeks (JLCPCB) | 4–6 weeks |
| Risk | LED board v0.2: WQFN-20 (0.4 mm pitch, exposed pad) and 0402s on an 18 mm double-sided board: stencil + hot plate or hot air only, not an iron | Part substitutions, rotations in the fab's preview, extended-part stock | Parts lost/kept by the fab, customs paperwork, uncut-tape rules |

## Recommendation

**Main board: Route 1** — bare boards + stencils from **PCBWay** (your stated preference; JLCPCB is ~£25 cheaper on
shipping and stencils) and Farnell parts. All main-board parts are 0603 or larger, SOT-23/SOIC, so a stencil + hot plate
or a fine iron does it. It is the cheapest by £100+ and the fastest.

**LED board v0.2: decide between two** (changed 2026-11-03 with the LP5012 redesign; the v0.1 board was all
TSSOP/0603):
- *Route 1, if you are set up for QFN work*: 0.10 mm bottom stencil, paste, place U1/U2/R1/C1–C4, hot plate (or hot air
  with preheat); inspect U1's corner pins with a loupe and check for EP bridging by continuity (handoff 05). Then the top:
  0.12 mm stencil or paste dots, D1–D9 and R2, hot air at low flow (the bottom parts stay put on surface tension).
  Order 5 boards and enough parts for 3–4 attempts (the BOM spares cover this).
- *Route 2 at JLCPCB for the LED board only, bottom side Economic* (U1, U2, R1, C1–C4; ~£10 + extended-part fees),
  then hand-fit the top: eight 2835s, one PLCC-4 and the 0402 R2 (easy with an iron and fine tweezers). Fill the
  LCSC column of `fab/led-board/v0.2/bom_jlcpcb.csv` from their part search. If LCSC has no LP5012RUKR, consign the
  DigiKey parts (Route 3 for that one line) or use JLC's global sourcing.

Recommended: **Route 2 for the LED board's bottom side** unless you already do QFNs; it removes the one fine-pitch
joint from the build for about £10–25.
**Route 3 is not worth it** at this quantity.
