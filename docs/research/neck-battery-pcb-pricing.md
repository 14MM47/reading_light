# Off-board sourcing and cost research: clip-on book light

Researched 2 Nov 2026. Nothing was ordered and no accounts were logged into.

**Labels.** Every number carries one of these:
- **[pub]**: published on the supplier's own page.
- **[page]**: quoted from a page or snippet that is not the supplier's own pricing page, such as a reseller, a forum or a search snippet.
- **[est]**: my estimate.
- **VERIFY**: the dimension or fact is not stated anywhere I could read.

**Access limits.**
- These sites refused automated fetches, so their figures come from search-result snippets only:
  - Farnell UK, CPC and Amazon UK (HTTP 503);
  - RS UK, desertcart and bigamart (HTTP 403);
  - conduit-flexible.com and atadiat.com (bot check).
- PCBWay's and JLCPCB's instant-quote calculators run on JavaScript and show $0.00 until used interactively, so none of the PCB totals below is a live quote.
- The web-search budget ran out near the end of section C. Farnell's UK delivery threshold and PCBWay's parts markup could not be checked again.
- Listings on Amazon, eBay and AliExpress are not stable. Re-check every listing before buying.

---

## A. Neck (gooseneck)

### Requirements recap
- Bendable length 100–150 mm (most goosenecks can't be cut).
- Outer diameter (OD) 5–10 mm.
- Hollow bore of at least 3.5 mm, ideally at least 4.5 mm.
- Holds about 20 g at 10 cm without drooping.
- Plastic-coated, black or white.
- Threaded or plain ends.

**Wire-fit check.** Four 1.0 mm round wires bundle inside a circle of (1+√2)·d ≈ 2.4 mm. Any bore of 3.5 mm or more passes the bare wires. A JST-SH 4-pin housing is about 6.0 × 2.9 mm [est] and will **not** pass a 4–5 mm bore. It only just might pass a 6.8 mm bore. So thread the bare wires through first and crimp or solder afterwards, or solder the wires to pads at both ends.

**Load check.** 20 g at 100 mm is about 0.02 N·m. Metal goosenecks of 8–10 mm OD are routinely sold as phone-holder or lamp arms carrying several times that [est]. Droop is unlikely, but VERIFY with the real moon.

### What exists (landscape)
| Source | What they have | Fit to brief |
|---|---|---|
| **Lamp Spares UK** (lampspares.co.uk, "Flexible Goosenecks" category) | 11 goosenecks, all M10×1 male both ends. Lengths 250 / 350 / 600 mm only. Finishes: brass, nickel, Old English and bronze plated. **None under 250 mm; none plastic-coated** [pub] | Too long; no coating. Best-documented UK stock. |
| **Dannells, Elstead, "lampshop"** | No gooseneck parts found in search | — |
| **RS Components UK** | Only RS PRO LED machine lights with 520 mm flexible necks (e.g. 777-7952, £91.88 ex VAT) [page]. No bare gooseneck or "flexible arm" part found | No |
| **Farnell UK / CPC** | PULSE microphone goosenecks PLS00077, 300 mm black (Farnell 3401830 / CPC ST01637), and PLS00079, 400 mm black (3401833 / ST01639). "Standard ⅝″ screw thread ends" [page] | Too long, ⅝″-27 mic thread, too fat |
| **Microphone goosenecks** | K&M 22260: 150 mm, black powder-coated steel, Ø15 mm, ⅜″ threads [page]. Gravity MA GOOSE S: 140 mm, ⅜″ [page]. Neumann SH 100 / SH 150 (MCM system) and Sennheiser MZH3015 (150 mm, XLR) [page] | Right length but 15 mm OD and ⅜″ or ⅝″ threads: too fat, heavy and expensive |
| **Amazon / Walmart / desertcart (PATIKIL, uxcell)** | Black or silver metal "Universal Gooseneck Hose" lines, M10 and M8×1 fine thread, 10 cm to 60 cm | **Best fit on size**; metal only, not plastic-coated |
| **Chuanghong Industrial** (flexiblegooseneck.com) | OEM maker. **PVC- or silicone-coated** goosenecks with M4/M6/M8/M10 thread options, made to length; request a quote at sales@flexiblegooseneck.com [pub] | The only coated, to-length source found; minimum order and price unknown (VERIFY) |
| **AliExpress** | e.g. "Black Metal Goose Neck Tube M8×6mm + M10×10mm Male Screw Thread Flexible Conduit" (10 × 400 mm) [page] | Usually 20–60 cm; no 10–15 cm coated listing confirmed |
| **Loc-Line ¼″** (plastic ball-segment hose) | ¼″ (6.35 mm) bore, about 16 mm OD [page] | Hollow and cuttable, but OD far too big |

### Top 3 options
| # | Supplier / product | URL | Length | OD | Bore ID | Ends / thread | Coating | Price | UK delivery |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **PATIKIL 4.7″ Universal Gooseneck**, M10 (sold singly) | listing seen via bigamart.com/?p=8159477 (403 to fetch; snippet only). Look for the same title on Amazon UK | **120 mm** overall [page] | **10 mm** [page] | **6.8 mm** [page] | M10 × 1 mm male (both ends VERIFY) | None: silver-tone metal [page] | £5–10 [est] | Amazon UK if listed (VERIFY), otherwise import |
| 2 | **PATIKIL 3.9″ Universal Gooseneck Hose, 2 pcs, M10 ext → M8 ext** | desertcart.com.ar/products/641125985-… (403; snippet only); Amazon US-type listing | **100 mm** [page] | **8 mm** [page] | **VERIFY**: "hollow, a wire of certain size can pass" [page]; 4–5 mm [est] | M10 × 1 male one end, M8 × **1.0 fine** male the other [page]. **Not** standard M8 × 1.25 nuts; not a mic thread | Black metal (paint or plate, not plastic: VERIFY) | about £8–12 for 2 [est] | VERIFY |
| 3 | **Lamp Spares UK: Nickel Plated Flexible Gooseneck M10×250 mm**, code 3285720 (£18.59); or Brass PLU10284 (£18.39, made by S. Lilley & Son, Birmingham) | lampspares.co.uk/nickel-plated-flexible-gooseneck-m10x250mm-3285720/ · lampspares.co.uk/m10x250mm-flexible-tube-raw-plu10284/ | **250 mm** excluding threads, 268 mm including [pub] | 11 mm (13 mm collars) [pub] | 6.5 mm in the spec, 5.5 mm in the notes, "max cable 5 mm" [pub] (conflict: VERIFY) | M10 × 1 male both ends [pub] | None (plated metal) | £18.59 / £18.39 incl. VAT [pub]; £1 off each at 10+ | UK stock; shipping from £4.89 [pub] |

Other near-misses:
- uxcell M10/M8 goosenecks: 8.3″ (210 mm, silver) and 9.8″ (250 mm, black), US$10.49 on Walmart [page].
- PATIKIL 9.9″ (25 cm), black, 2 pcs, M10 male → M10 female, 10 mm OD, US$23.99 [page].
- Coolbe 20 cm, black, M8 → M10 male, 10 mm OD, 2 pcs [page].

### Coating
None of the ready-made 10–15 cm parts is plastic-coated. Plan to sleeve one:
- **Black or white heat-shrink**: 2:1 or 3:1. Thin-wall 12 mm shrinks onto 10 mm OD; 9.5 mm suits 8 mm OD.
- **Or a slip-on silicone tube**: 8 mm ID over the 8 mm part, 10 mm ID over the 10 mm part.

Either adds about 0.3–0.6 mm of wall [est] and gives a soft, matte, "coated" look. A coated part made to length needs an OEM such as Chuanghong (minimum order and price VERIFY).

### Mounting
- The M10×1 male end screws into a printed M10×1 boss, or a brass M10 lamp nut on the pack lid.
- Lamp Spares also sells M10 hollow plastic rods and nuts: an M10 black plastic hollow rod of 10 mm or 30 mm, quoted bore 7.2 mm [page].
- The M8×1 fine end needs a fine-pitch tap or nut. Standard M8 (1.25) nuts won't fit [page].

### DIY fallback (armature wire + silicone sleeve)
**Spine.** One length of 3.17–3.2 mm round aluminium armature wire, or two lengths of 2 mm.
- Tiranti 3.17 mm round, from Pottery Crafts: "from £2.71 ex VAT" [page]; length per price is VERIFY.
- Flints WIR078, 3.2 mm × 10 m: £11.38 ex VAT [page].
- Fred Aldous 3.2 mm, 500 g: £20.52 [page].

**Sleeve.** Black or white silicone tube about 6 mm ID × 8 mm OD, from RS PRO or Amazon (specific part VERIFY).
- Run the armature and the four Qwiic wires inside the sleeve.
- Glue the ends into printed sockets.

**Strength check.** Elastic yield moment of 3.2 mm soft aluminium is about 0.1 N·m [est], about 5× the 0.02 N·m needed.

**Risk.** Aluminium work-hardens and snaps after many bend cycles. Solid copper (2 × 2.5 mm² earth conductor) is a tougher alternative [est].

### Recommendation (A)
- **Primary: PATIKIL 4.7″ / 120 mm M10 gooseneck.**
  - It is the only short part with a *stated* bore (6.8 mm, roughly 3× the wire bundle).
  - 10 mm OD is at the top of the range.
  - M10×1 threads mate with standard lamp nuts.
  - Sleeve it in black or white heat-shrink or silicone for the coated look.
- **Backup: PATIKIL 3.9″ / 100 mm, 8 mm OD, black, M10/M8×1, 2-pack.**
  - Slimmer and closer to the 100 mm target.
  - The bore is unstated (VERIFY on arrival). Expect 4–5 mm: enough for bare wires, not connectors.
- **Fallback:**
  - The Lamp Spares 250 mm part only if a longer neck becomes acceptable (UK stock, best-specified).
  - Otherwise the DIY armature-plus-silicone build.
  - For a coated part made to length later, request a quote from Chuanghong.

---

## B. Battery: 3.7 V LiPo pouch, about 1200 mAh, protection circuit (PCM), JST-PH 2.0 mm 2-pin, no larger than 6 × 36 × 64 mm

| Supplier | Code | Size (T × W × L) | Connector & lead | PCM | Max charge | NTC | Price | Notes |
|---|---|---|---|---|---|---|---|---|
| **Pimoroni** "LiPo Battery Pack 1200mAh" | **BAT0004** | 5.3 × 35.5 × 64 mm [pub] (fits with **zero** length margin; VERIFY with calipers) | "2-pole JST" (PH 2.0 VERIFY), 100 mm lead [pub] | Yes: short-circuit, 4.2 V charge cut-off, 2.4 V discharge cut-off [pub] | Not stated (datasheet linked; VERIFY) | Not stated (assume none) | **£8.25** [pub] | Bare cells ship to UK and mainland Europe only [pub]. 4.9★ from 31–34 reviews [page]. A pre-order / "Notify me" notice was shown; stock VERIFY |
| **The Pi Hut** "1200mAh 3.7V LiPo Battery – JST-PH Connector" (PKCell; datasheet file LP503562) | **105188** | 5 × 35 × 62 mm [pub] | JST-PH 2 mm, about 100 mm cable [pub] | Yes: "internal protection against over-charging and under-voltage", cuts out about 3 V [pub] | Not stated. Discharge 0.5–1 C (0.5 C recommended) [pub] | Not mentioned | **£8** (sale, incl. VAT) [pub] | "Only 12 units left" on my fetch, while an earlier snippet said sold out: volatile. **Ships only within England/Wales, DHL only** [pub]. IEC 62133 / CE |
| **Adafruit 258** "Lithium Ion Polymer Battery – 3.7v 1200mAh" | 258 | 5 × 34 × 62 mm, 23 g [pub] | JST-PH 2-pin, cable rated 2 A [pub] | Yes: over-charge, over-discharge, short; cuts out at 3.0 V [pub] | **500 mA max (about 0.5 C)** [pub] | **No** ("like most lipos… do not have thermistors") [pub] | US$9.95 (1–9) [pub] | **No UK route confirmed.** No Farnell or RS UK listing surfaced (both block fetches; VERIFY on site). Mouser UK says it is "unable to sell this product in your country" [page]. The Pi Hut search returned nothing |
| RS UK | RS PRO 3.7 V 1 Ah pack, 176-9376 | — | Flying leads, not JST [page] | — | — | — | — | Being discontinued [page]. No suitable JST-PH 1200 mAh pouch found at RS |
| Farnell / CPC / Rapid / Cool Components | — | — | — | — | — | — | — | Nothing found in search (VERIFY on site). Farnell lists Pimoroni boards but not this battery |

### Polarity (JST-PH inconsistency)
- **Adafruit, SparkFun and Particle all agree.** Look into the plug's mating face with the narrow key or latch ridge on top: **red (+) is on the right** [page: Digi-Key forum; Particle community]. So yes to the brief's question, *viewed into the mating face with the latch up*.
- **Other vendors are inconsistent.** "About half" of vendors are reversed [page: Maker.io / RobotShop]. The Pi Hut itself warns "always (always!) double-check" and suggests swapping pins [pub].
- **Design actions:**
  - Lay the board connector out to Adafruit's convention.
  - Put "+" and "−" on the silkscreen next to it.
  - Meter every new pack before first plug-in.
  - PH crimps can be lifted out and swapped by pressing the housing tab.

### NTC
None of the 2-wire JST-PH packs has a thermistor. 3-wire "603450 NTC" packs exist, but they usually come with JST-SH 1.0 or other 3-pin connectors [page].
- If the charger IC has a TS pin, tie it off per its datasheet (often 10 kΩ to GND) [est].
- Otherwise sense the cell temperature on the main board.

### Charge current
Set charge current to **400–500 mA** (no more than 0.5 C of 1200 mAh). That is safe across all three vendors. Adafruit caps at 500 mA; PKCell recommends 0.5 C.

### Recommendation (B)
- **Primary: Pimoroni BAT0004** (£8.25, UK seller, published PCM spec). It meets the 64 mm length limit exactly, so VERIFY the real pouch length and lead exit against the 42 × 74 × 18 mm pack.
- **Backup: The Pi Hut 105188** (£8, 62 mm long so 2 mm margin, explicit JST-PH). Note the England/Wales-only, DHL-only shipping.
- **Adafruit 258** is the reference part (500 mA max charge, no NTC) but is not practically buyable in the UK today.
- Design the board for **either polarity risk** (silkscreen, plus reverse-polarity protection on the battery input if board space allows).

---

## C. PCB cost comparison: PCBWay (three routes) and JLCPCB (routes 1 and 2)

### Assumptions
- **Boards:**
  - MAIN: 32 × 56 mm, 2-layer, 1.6 mm, HASL-LF or ENIG, about 35 SMD parts on one side, 1 × USB-C.
  - LED: Ø24 mm, 2-layer, 1.0–1.6 mm, white solder mask, about 20 parts on **both** sides (LEDs on top, LP5012PWR TSSOP-24 plus passives on the bottom).
- **Quantity:** 5 of each.
- **Exchange rate:** £1 ≈ US$1.30 [est; check the current rate].
- **LP5012PWR is confirmed TSSOP-24 (PW)** [page: LCSC, DigiKey].
  - LCSC C1518705: US$1.414 @1, $1.276 @10 [page]. One LCSC page showed only 89 in stock (VERIFY).
  - DigiKey UK about £0.90 @1 [page].
  - At JLCPCB it is not a Basic part, so it is Extended [est].

### Published fee facts used
**PCBWay**
- Bare PCB "from $5 / 10 pcs" (100 × 100 mm, 2-layer, 1.6 mm) [pub, homepage].
- Assembly "from $29", "Only $29 in total for 1–20pcs assembly", "$29 free shipping for 1–20pcs assembly" [pub, homepage]. Eligibility terms are not stated.
  - One comparison article reads this as SMT labour and setup only; PCB and parts excluded [page: lead-pcb.com].
  - One 2026 turnkey report saw a $29 assembly fee roughly offset by a shipping discount [page: wereallgeeks].
- **Stencils:**
  - Framed 370 × 470 mm: $15 [pub].
  - "Valid area 190 × 290 mm: $10.00" [page: PCBWay assembly page text]. That is probably the custom or non-framed size.
  - Framed stencils are "more expensive to ship… dimensional weight" [pub].
- **Assembly quote coverage:** "tooling, laser cut steel stencil, and labor"; "in case of Turn-key… the cost of parts will be added" [pub, assembly FAQ]. The pre-approval price is "assembly only" [pub, help centre].
- **Small boards:** "Panelization is needed when your PCB dimension is smaller than 50mm×100mm" [pub, assembly FAQ]. **Both boards are smaller, so both need panels or rails** (extra PCB area and engineering).
- **Consigned parts:**
  - Passives 0603–2225, SOT, SOD and MELF: "minimum of 50 pieces and… exceed the required quantity by 30 pieces".
  - 0402: minimum 100 and +50.
  - ICs and connectors: "1–5 pieces" extra.
  - Strips must not be cut; label each part with its BOM line; include a packing list.
  - Unused parts are not returned by default [all pub, assembly FAQ].
- **Lead time:** quote "within 1 business day" [pub, PCBWay blog 2020]. PCBA build "3–5 days", counted from when parts and PCBs are ready [pub].
- **Parts markup:** "20–300% over the LCSC or DigiKey price", from one 2021 user report [page: EEVblog]. No official percentage is published.
- **VAT:** PCBWay's own help page says "You are responsible to clear VAT" [pub, 2018 page]. A 2021 forum report says PCBWay and JLCPCB collect VAT at order time for UK orders under £135 [page].
  - UK rules require overseas sellers to collect VAT at checkout on consignments of £135 or less. Above £135, VAT plus any duty is collected at import, with a courier handling fee (e.g. "£11" reported for DHL) [page].
  - **Whether PCBWay adds UK VAT at checkout today: VERIFY at checkout.**
  - PCBWay's 2020 "PCBWayExpress-IP" UK route was DDP (duties paid up front), B2C only, ≤US$165 declared [pub].
- **Shipping:** No UK rate is published. DHL takes 3–7 business days [pub].
  - Older UK forum reports: about $25–26 DHL for a few small boards [page], plus surprise DHL VAT and handling bills when VAT was not prepaid [page].

**JLCPCB** (help page "Last updated on Oct 22, 2026") [pub]

| Fee | Economic PCBA | Standard PCBA |
|---|---|---|
| Sides | Single-sided only | Single or double-sided |
| Setup | $8.18 | $25.56 single / **$51.12 double** |
| Stencil | $1.53 | $8.21 single / **$16.42 double** |
| SMT placement | $0.0016 per joint | $0.0016 per joint |
| Feeder loading | **$3.07 per unique Extended part** (Basic and Preferred-Extended free) | **$1.53 per unique part** (Basic or Extended) |
| Packing | Free | $0.50 + area |
| Build time | 1–3 days | 4 days or more |

- Both tiers: hand-soldering labour $3.58 per order; manual joints $0.0164 each; "confirm parts placement" $0.45.
- Standard tier also lists "rigid PCB fixtures: 1–29 pcs: 2 fixtures, $16.42". Whether this applies to a plain SMT order is VERIFY.
- Bare PCB "$2 for 5 boards" (via the JLCONE desktop app; about $4 on the web) [page].
- Small custom stencil (≤100 × 100 mm, frameless) $3 [pub, title of JLCPCB "Small SMT Stencil Only $3" page].
- **UK VAT**: £0–135 for **individual** customers, "VAT collected by JLCPCB". For companies, or orders above £135, "collected by local customs" [pub].

### Route 1: bare PCBs + stencils, parts from Farnell, hand assembly (5 + 5)
| Line | PCBWay | JLCPCB | Label |
|---|---|---|---|
| PCB MAIN (5 pcs) | $5 base (+ lead-free HASL about $0–5, or ENIG about +$10–20) | $2–4 (ENIG about +$8–15) | base [pub]; uplifts [est] |
| PCB LED, round, white solder mask (5 pcs) | $5 base (white about +$0, +1–2 days; 1.0 mm about +$0) | $2–4 (white about free) | base [pub]; uplifts [est] |
| Stencils (MAIN top; LED top + bottom on one sheet) | 2 × about $10 non-framed (2 × $15 framed, heavy to ship) | 2–3 × $3 | [page] / [pub] |
| Shipping to UK (one parcel) | DHL about $20–30 | Global Standard Direct about $5–15, or DHL about $15–25 | [est] |
| **Subtotal ex VAT** | **about $45–90 ≈ £35–70** | **about $15–50 ≈ £12–38** | [est] |
| UK VAT 20% | £7–14 (checkout or import: VERIFY) | £2–8 (JLCPCB collects for individuals ≤£135) | rule |
| Farnell parts for 5 + 5 boards, incl. VAT | about £70–120 | same | [est]; depends on real BOM, cut-tape minimums and line count |
| Solder paste / consumables | about £10–20 | same | [est] |
| **Route 1 total** | **about £120–225** | **about £95–185** | [est] |
| Qty 10 + 10 | PCB and stencil cost barely changes ($5 covers 10 pcs). Parts about ×1.7, so **about £170–330** | **about £145–290** | [est] |

Hand-assembling the double-sided LED board: paste and reflow the bottom (TSSOP-24 and passives) first. Then do the top LEDs with a dispensed paste and hot air, or a low-temperature paste [est].

### Route 2: PCBWay turnkey PCBA (PCBWay sources parts) vs JLCPCB PCBA (LCSC parts)
| Line | PCBWay turnkey | JLCPCB | Label |
|---|---|---|---|
| Assembly / setup MAIN (single side) | $29 promo if eligible (VERIFY); otherwise about $60–90 | Economic: $8.18 setup + $1.53 stencil + about 1,000 joints × $0.0016 = $1.60 | [pub] / [est] |
| Assembly / setup LED (**two-sided**) | Promo eligibility doubtful; about $88–150 for two-sided | Standard double: $51.12 + $16.42 stencil + 350 joints ≈ $0.56 + packing about $0.6 | [page third-party "$88–150"] / [pub] |
| Stencil | Included in the assembly quote | Included above | [pub] |
| Feeder / extended-part fees | Not itemised | MAIN: about 5 Extended × $3.07 ≈ $15. LED: about 8 unique × $1.53 ≈ $12 | [pub] rates, [est] counts |
| USB-C through-hole legs (if any) | Quoted | $3.58 labour + manual joints | [pub] |
| PCBs (panelised, ENIG and white options) | about $10–40 per design (panels required below 50 × 100 mm) | about $4–20 per design | [est] |
| Parts (5 + 5 boards plus attrition) | about $90–160 (markup 20–300% reported) | about $45–80 at LCSC prices (LP5012 about $1.3–1.4 each) | [est] |
| Shipping to UK | "free shipping for 1–20 pcs assembly" with the promo; otherwise DHL about $25–35 | DHL about $20–30 | [pub] / [est] |
| **Subtotal ex VAT** | **about $230–480 ≈ £175–370** (likely about £220) | **about $175–265 ≈ £135–205** (likely about £160) | [est] |
| UK VAT 20%, plus a courier fee if over £135 and not prepaid | +£35–75 (+ about £11 handling) | +£27–41 (+ about £11 if over £135) | rule / [page] |
| **Route 2 total incl. VAT** | **about £210–455** | **about £165–260** | [est] |
| Lead time, door to door | Quote 1 day + parts sourcing about 1–2 weeks + PCBA 3–5 days + DHL 3–7 days ≈ **3–4 weeks** | Parts usually in stock; build 1–3 days (Economic) / 4+ (Standard) + DHL ≈ **1.5–2.5 weeks** | [pub] / [est] |
| Qty 10 + 10 | Setup roughly fixed, so about £280–600 | about £210–330 | [est] |

**JLCPCB saving.** Put only the bottom side of the LED board (LP5012 and passives) through **Economic** single-sided assembly, then hand-solder the few top-side LEDs. That drops Standard's $51.12 + $16.42 to $8.18 + $1.53, **saving about $58 (≈ £45)** [pub rates].

**Small-board rules.** Minimum board size and edge-rail rules for JLCPCB Standard and Economic are VERIFY. Expect to panelise the Ø24 mm board, e.g. a 2 × 2 or 3 × 3 panel with rails.

### Route 3: PCBWay PCBA with consigned (customer-supplied) parts
| Line | Estimate | Label |
|---|---|---|
| Assembly + PCBs + return shipping | Same as route 2 without parts: **about $130–320 ≈ £100–245** | [est] |
| Parts from Farnell incl. PCBWay overage | Each passive line needs at least 50 pcs and the required quantity +30. ICs +1–5 each. **About £90–150 incl. VAT** | [pub] rule, [est] cost |
| Courier UK → PCBWay (Shenzhen), about 0.5–1 kg | **About £30–70** express (DHL/FedEx/UPS via a broker, about 3–7 days); cheaper post is slow and risky | [est] |
| China-side risks | Import paperwork or duty and delay; strips must stay uncut and labelled to BOM line; parts not returned by default | [pub] / [est] |
| UK VAT on the returning assembly | 20% on the declared value. Whether customs counts your consigned parts in that value is VERIFY | [est] |
| **Route 3 total** | **about £250–500**, and the slowest (+1–2 weeks) | [est] |

### Recommendation (C)
- **First prototype spin (5 + 5): Route 1 at JLCPCB.** Bare boards plus $3 frameless stencils, about £20–45 delivered with VAT. Parts from Farnell, about £70–120.
  - Cheapest cash outlay.
  - Both boards are easy hand-builds; the LED board needs a bottom-then-top reflow.
  - PCBWay route 1 is about £25–35 dearer, mostly shipping.
- **If you want boards assembled: JLCPCB route 2.**
  - Economic for the MAIN board.
  - Economic bottom-side-only for the LED board, with the LEDs hand-fitted.
  - About £120–200 all-in, versus about £165–260 with Standard double-sided.
- **Use PCBWay turnkey** only if its $29 1–20-pc promo is confirmed for these designs, or if parts are missing from LCSC.
- **Route 3 is not worth it at this quantity.** The overage minimums plus the courier to China outweigh any parts saving.
- **Before ordering:**
  - Run both instant quotes with real Gerbers and BOMs; the calculators are free.
  - Check UK VAT is shown at checkout, as an individual buyer, for orders of £135 or less.
  - Check LP5012PWR stock at LCSC (C1518705).

---

## Sources

**A. Neck**
- https://www.lampspares.co.uk/flexible-goosenecks/
- https://www.lampspares.co.uk/m10x250mm-flexible-tube-raw-plu10284/
- https://www.lampspares.co.uk/nickel-plated-flexible-gooseneck-m10x250mm-3285720/
- https://lampspares.co.uk/m10-black-plastic-threaded-hollow-rod-30mm-9157269
- https://lampspares.co.uk/10mm-black-plastic-threaded-hollow-rod-10mm-long
- https://bigamart.com/?p=8159477 (PATIKIL 4.7″; snippet only)
- https://desertcart.com.ar/products/641125985-patikil-3-9-universal-gooseneck-hose-2-pcs-m10-to (snippet only)
- https://bigamart.com/?p=11831391 (PATIKIL 9.9″; snippet only)
- https://www.walmart.com/ip/5553810108
- https://www.walmart.com/ip/Uxcell-8-3-Metal-Gooseneck-M10-M8-Thread-Metal-Hose-Flexible-Arm-Gooseneck-Tube-Extension-for-Lamp-Phone-Holder-DIY/1573136895
- https://www.coolbe.co.nl/cs/products/687079c922574d01ea6dd957 (snippet; page now 404)
- https://www.aliexpress.us/item/2255801062372953.html
- https://flexiblegooseneck.com/pvc-coated-gooseneck-tube/
- https://flexiblegooseneck.com/flexible-gooseneck-black-plated-tubing/
- https://uk.rs-online.com/web/p/products/7777952
- https://uk.farnell.com/pulse/pls00077/gooseneck-300mm-black/dp/3401830
- https://cpc.farnell.com/pulse/pls00079/gooseneck-400mm-black/dp/ST01639
- https://www.huss-licht-ton.de/product_info.php/en/K-M-22260-Gooseneck-150mm/info/58700.html
- https://www.neumann.com/en-ae/products/microphone-accessories/sh-150
- https://www.thomann.co.uk/sennheiser_mzh3015_schwanenhals.htm
- https://diynot.com/diy/threads/what-thread-on-my-gooseneck.618377
- https://potterycrafts.co.uk/products/tiranti-round-aluminium-armature-wire-3-17mm
- https://www.flints.co.uk/product/All/WIR078
- https://www.fredaldous.co.uk/products/aluminium-wire-3-2mm-500g
- https://aimsindustrial.com.au/products/loc-line-1-4-modular-hose-segment

**B. Battery**
- https://shop.pimoroni.com/products/lipo-battery-pack (prices from the page's .json)
- https://thepihut.com/products/1200mah-3-7v-lipo-battery
- https://www.adafruit.com/product/258
- https://www.mouser.com/ProductDetail/485-258
- https://uk.rs-online.com/web/p/rechargeable-battery-packs/1769376
- https://botland.store/withdrawn-products/20147-1200mah-37v-li-pol-pimoroni-battery-jst-connector-64x355x53mm-5903351240369.html
- https://forum.digikey.com/t/polarity-standard-for-jst-ph-connectors-on-lipo-batteries/64548
- https://community.particle.io/t/why-isnt-battery-polarity-always-the-same-in-jst-pins/44474
- https://community.robotshop.com/tutorials/show/reversing-the-polarity-on-lipo-battery-jst-connectors
- https://www.ebay.de/itm/112702247608 (603450 NTC 3-wire)

**C. PCBs**
- https://www.pcbway.com/
- https://www.pcbway.com/pcb-assembly.html
- https://www.pcbway.com/assembly-faq.html
- https://www.pcbway.com/quotesmt.aspx
- https://www.pcbway.com/stencil.aspx
- https://www.pcbway.com/pcb_prototype/SMT_stencil_and_Laser_Stencil.html
- https://www.pcbway.com/helpcenter/pcb_assembly_ordering/Assembly_cost_will_be_showed_after_submit_order_is_components_cost_included_.html
- https://www.pcbway.com/blog/PCB_Basic_Information/PCBWay_Q_A_003___Common_Questions_for_PCBA_Ordering_01.html
- https://www.pcbway.com/helpcenter/Findproducts/Do_I_have_to_pay_for_customs_and_import_taxes_.html
- https://www.pcbway.com/blog/Activities/PCBWayExpress___European_Exclusive_Route_Logistic.html
- https://www.pcbway.com/shipping_method_guide.aspx
- https://wereallgeeks.wordpress.com/2026/08/20/pcbways-all-inclusive-turnkey-pcb/
- https://lead-pcb.com/blog/jlcpcb-vs-pcbway/
- https://pamfinds.pages.dev/guides/best-pcb-assembly-services/ (third-party, unsourced figures)
- https://www.eevblog.com/forum/manufacture/turnkey-assembly-costs-price-check/
- https://www.eevblog.com/forum/manufacture/good-pcb-houses-for-uk-buyers/msg3915650/
- https://forum.allaboutcircuits.com/threads/pcbway-ultra-low-cost-pc-boards.156773/
- https://www.model-engineer.co.uk/forums/topic/dhl-rip-off
- https://jlcpcb.com/help/article/pcb-assembly-price
- https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype
- https://jlcpcb.com/help/article/18-Customs,-Duties-and-Taxes
- https://jlcpcb.com/resources/small-stencil
- https://jlcpcb.com/help/article/76-How-much-does-shipping-cost
- https://www.lcsc.com/product-detail/C1518705.html
- https://www.digikey.co.uk/en/products/detail/texas-instruments/LP5012PWR/13542555
