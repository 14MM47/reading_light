# 02: Parts order

Quantities are for **2 complete lamps plus spares**. To regenerate for another quantity, run
`python3 bom/build_bom.py --sets N` in the repo and then re-run the deliverable generator.

| File | Use |
|---|---|
| `farnell_quickpaste.txt` | Paste into Farnell UK **Quick Paste / BOM upload** (31 lines: order code or MPN, quantity) |
| `farnell_order.csv` | The same basket with MPNs, indicative prices and notes |
| `digikey_order.csv` | Parts Farnell does not stock: the TI LP5012RUKR (WQFN-20) from DigiKey UK |
| `other_purchases.csv` | Not from Farnell: LiPo, gooseneck, cable kit (RS), nut, screws, sleeve, Kapton, CA, silicone, filament, programmer |
| `ORDER-summary.pdf` / `.md` | Human summary with totals |
| `BOM.csv` | Every line on both boards, plus the off-board parts, per lamp |
| `assembly-routes-cost-comparison.pdf` | Bare boards + hand assembly vs fab turnkey vs consigned parts |

Indicative total: Farnell ≈ £47 + DigiKey ≈ £15 + other ≈ £85 + programmer ≈ £15 (if needed) + PCBs ≈ £15–60 + LED bottom-face assembly ≈ £10–25 → ≈ £160–247 for 2 lamps. (If the fab sources the LP5012 from LCSC, drop the DigiKey line.)

Lines marked "(search MPN)" need the exact MPN picked on the Farnell site. The substitution rules are in
`handoff-02-parts-order.pdf`.
