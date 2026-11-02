# Handoff 02 — Parts order

**For:** Claude Code in VS Code with Matt at the browser. ~20 min. **Matt places the order.**

1. Run `python3 bom/build_bom.py --sets 2`. It regenerates every list from the board designs (default: 2 lamps +
   spares). Read `bom/ORDER.md` first: it is the human summary, with indicative totals.
2. Farnell UK (uk.farnell.com, or CPC for personal accounts): use **Quick Paste / BOM upload** with
   `bom/farnell_quickpaste.txt` (order code or MPN, quantity). Lines marked "(search MPN)" need their Farnell code
   picked on the site — choose the exact MPN; if out of stock, any 0603 1 % thick-film resistor of the same value,
   or an X5R/X7R ceramic of the same value, voltage ≥ listed and the same case size, is fine.
3. Check stock on: TLC59116IPWR (3119169), Bridgelux BXEN 2700 K (3498849 — only a few hundred were listed),
   LM75BDP,118. If BXEN 2700 K is out, use BXEN-27S-11M-3C at any flux bin; if LM75BDP is out, PCT2075DP,118 is a
   drop-in (same TSSOP-8 pinout and register map).
4. Other purchases are in `bom/other_purchases.csv`: battery, gooseneck, silicone sleeve, M10 nut, the Qwiic cable
   kit from RS, screws and filament. It also lists the assembly consumables from round 1: PTFE sleeve, Kapton tape,
   CA gel, neutral-cure silicone, and a ≥ 1 A USB-C charger if you don't have one.
   * Gooseneck: confirm the listing says M10 thread on both ends and a hollow bore. We need ≥ 4.5 mm for the cable in
     its PTFE sleeve.
   * Battery: protected cell (PCM), JST-PH 2.0 lead. Polarity varies between sellers, so meter it on arrival
     (VERIFY E1).
5. Optional tool: MPLAB SNAP (Farnell 2915518) or a 3.3 V USB-UART for SerialUPDI (handoff 04).

## Done when
Orders are placed, and the actual codes and prices are recorded in `bom/ORDER_ACTUALS.md`. `ORDER.md` is
generated, so don't edit it.
