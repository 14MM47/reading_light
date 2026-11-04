# Handoff 02 — Parts order

**For:** Claude Code in VS Code with Matt at the browser. ~20 min. **Matt places the order.**

1. Run `python3 bom/build_bom.py --sets 2`. It regenerates every list from the board designs (default: 2 lamps +
   spares). Read `bom/ORDER.md` first: it is the human summary, with indicative totals.
2. Farnell UK (uk.farnell.com, or CPC for personal accounts): use **Quick Paste / BOM upload** with
   `bom/farnell_quickpaste.txt` (order code or MPN, quantity). Lines marked "(search MPN)" need their Farnell code
   picked on the site — choose the exact MPN; if out of stock, any 1 % thick-film resistor of the same value **and
   the same case size** (0603 on the main board, **0402** for R1/R2 on the LED board), or an X5R/X7R ceramic of the
   same value, voltage ≥ listed and the same case size, is fine.
3. Check stock on: Bridgelux BXEN 2700 K (3498849 — only a few hundred were listed) and MCP9800A0T-M/OT (1439485).
   If BXEN 2700 K is out, use BXEN-27S-11M-3C at any flux bin. The MCP9800 must be the **A0** address variant in
   **SOT-23-5**. If it is out, the **MCP9802A0T-M/OT** is a drop-in (same SOT-23-5 pinout, address and registers; it
   adds a 35 ms bus time-out, which is harmless here). The MCP9801/03 are 8-pin parts and do not fit.
4. DigiKey UK (digikey.co.uk): the **TI LP5012RUKR** (WQFN-20, cut tape), which Farnell and RS do not stock;
   `bom/digikey_order.csv` / ORDER.md §1b. Make sure the suffix is **RUK** (WQFN): the LP5012PWR is the TSSOP-24
   and does not fit. If you choose fab assembly for the LED board (handoff 01), let the fab source it (LCSC) or
   consign these, and skip this line.
5. Other purchases are in `bom/other_purchases.csv`: battery, gooseneck, silicone sleeve, M10 nut, the Qwiic cable
   kit from RS, screws and filament. It also lists the assembly consumables from round 1: PTFE sleeve, Kapton tape,
   CA gel, neutral-cure silicone, and a ≥ 1 A USB-C charger if you don't have one.
   * Gooseneck: confirm the listing says M10 thread on both ends and a hollow bore. We need ≥ 4.5 mm for the cable in
     its PTFE sleeve.
   * Battery: protected cell (PCM), JST-PH 2.0 lead. Polarity varies between sellers, so meter it on arrival
     (VERIFY E1).
6. Optional tool: MPLAB SNAP (Farnell 2915518) or a 3.3 V USB-UART for SerialUPDI (handoff 04).

## Done when
Orders are placed, and the actual codes and prices are recorded in `bom/ORDER_ACTUALS.md`. `ORDER.md` is
generated, so don't edit it.
