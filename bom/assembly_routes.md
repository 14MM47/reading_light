# Assembly routes — price comparison (you asked to "discuss price difference of all 3 options")

Quantities: 5 main boards + 5 LED boards (fabs' minimum batch), parts for **2 complete lamps** + spares (bare-board
route) or 5 + 5 populated boards (assembly routes). GBP incl. 20 % VAT, £1 ≈ US$1.30. **All figures are estimates from
published fee tables and recent user reports (2025–2026); run the fabs' instant quotes with the real Gerbers/BOMs
before ordering.** Detail and sources: `docs/research/neck-battery-pcb-pricing.md` §C.

| | Route 1: bare PCBs + stencils, Farnell parts, hand assembly | Route 2: fab turnkey assembly (fab sources parts) | Route 3: fab assembly with consigned Farnell parts |
|---|---|---|---|
| PCBs (5 + 5) | PCBWay £10–20 / JLCPCB £5–12 | panelised (both boards < 50 × 100 mm) £8–30 | as route 2 |
| Stencils | PCBWay ~£16 (2 × frameless) / JLCPCB ~£5 | included | included |
| Assembly fees | — (your time: ~1.5 h per lamp) | PCBWay ~£45–70 single-side + £70–115 double-side (LED board); **$29 1–20 pc promo if it applies** / JLCPCB: Economic main board ~£10, LED board Standard double-sided ~£55 (or Economic bottom-only ~£10 + hand-fit the top LEDs) | as route 2 |
| Parts | Farnell **~£53** for 2 lamps + spares (`bom/farnell_order.csv`, £44 ex VAT) | PCBWay £70–125 (markup 20–300 % reported) / JLCPCB £35–60 (LCSC; TLC59116, Bridgelux, Würth are "extended" parts, ~£2.40 feeder fee each) | Farnell £70–115 incl. the fab's overage rules (≥50 pcs per passive line, +30) |
| Shipping | DHL £15–25 (PCBWay) / £5–15 (JLCPCB post) | £15–25 (PCBWay promo may include) | + courier UK → Shenzhen **£30–70** |
| **Total (5 + 5 boards)** | **PCBWay ~£95–140, JLCPCB ~£70–100** (+ solder paste ~£10 if you have none) | **PCBWay ~£210–450 (likely ~£260), JLCPCB ~£150–250** | **~£250–500**, slowest (+1–2 weeks) |
| Lead time to boards in hand | 1–2 weeks | 2.5–4 weeks (PCBWay) / 1.5–2.5 weeks (JLCPCB) | 4–6 weeks |
| Risk | Hand-soldering TSSOP-28/TSSOP-8 and the double-sided LED board (bottom first, then LEDs with hot air) | Part substitutions, rotations in the fab's preview, extended-part stock | Parts lost/kept by the fab, customs paperwork, uncut-tape rules |

## Recommendation (chosen for this build)
**Route 1** — bare boards + stencils from **PCBWay** (your stated preference; JLCPCB is ~£25 cheaper on shipping and
stencils if you don't mind) and every part from Farnell. It is the cheapest by £100+, the fastest, and it is what the
Farnell order list was built for. All parts are 0603 or larger, SOT-23/SOIC/TSSOP, no QFN/BGA, so a stencil + hot plate or
a fine iron does it.

Pick **Route 2 at JLCPCB** instead if you'd rather not solder the TLC59116 (TSSOP-28, 0.65 mm pitch) and the LED board:
Economic assembly for the main board, Economic bottom-side-only for the LED board, then hand-fit the ten top-side LEDs
(2835/PLCC-4 are easy). Fill the LCSC column of `fab/*/v0.1/bom_jlcpcb.csv` from their part search.
**Route 3 is not worth it** at this quantity.
