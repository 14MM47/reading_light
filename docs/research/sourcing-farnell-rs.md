# Reading lamp: UK sourcing research (Farnell UK first, RS UK as fallback)

Researched 2 Nov 2026. No orders were placed and nothing was logged into.

## How to read the "Verified?" column

| Tag | Meaning |
|---|---|
| **C** | Order code verified: it appeared in a distributor product URL (`/dp/<code>` on Farnell, `/web/p/.../<code>` on RS, `/dp/SCxxxxx` on CPC). |
| **P\*** | Price or stock comes from the search engine's cached copy of the distributor page. Farnell and RS block direct fetches (403/503), so these figures are undated, sometimes contradict each other, and are indicative only. Confirm on the live page. |
| **DK** | Live DigiKey UK fetch on 2 Nov 2026, used to sanity-check price and lifecycle. These are DigiKey prices, not Farnell's. |
| **DS** | Read from the manufacturer datasheet. |
| **U** | Unverified. |

Farnell prices are GBP **ex VAT**. "@5+" means the price break at 5 units and above (minimum order is often 5 or 10 on cut tape). "—" means not seen.

---

## 1. I2C constant-current LED driver (≥11 ch, ≥30 mA, TSSOP/HTSSOP)

| Distributor | Order code | MPN | Mfr | Package | Price qty1 / qty10 | Stock / lead | Lifecycle | Source URL | Verified? |
|---|---|---|---|---|---|---|---|---|---|
| Farnell | **not found** | LP5012PWR | TI | TSSOP (DK lists "24-TSSOP"; check pin count against TI datasheet) | DK £1.18 / £0.864 | DK 1,781 | Active (DK) | Not in Farnell or RS search index (3 queries) | DK only |
| Farnell | **not found** | LP5009PWR | TI | TSSOP | DK £0.81 / £0.587 | DK 5,900 | Active (DK) | — | DK. **Only 9 outputs, so it fails ≥11 ch** |
| Farnell | **2759859** | PCA9955BTWJ | NXP | HTSSOP-28 (exposed pad) | P\* £2.68 / £2.28 | P\* 14,550, but the same cached page also shows "No Longer Manufactured" (2022-era text) | DK: Active, 28,575 in stock, £1.99 / £1.477 | https://uk.farnell.com/nxp/pca9955btwj/led-driver-constant-current-htssop/dp/2759859 | C, P\* (conflicting), DK |
| Farnell | 2890538 | PCA9955BTW/Q900J | NXP | HTSSOP-28 | DK £2.64 (single price) | — | U | https://uk.farnell.com/nxp/pca9955btw-q900j/fm-i2c-bus-led-driver-16-ch-htssop/dp/2890538 | C |
| Farnell | **3119169** | TLC59116IPWR | TI | TSSOP-28 (no pad) | P\* £1.89 / £1.41 | P\* 1,988 in stock, 16-wk standard lead | DK: Active, 3,701, £2.00 / £1.484 | https://uk.farnell.com/texas-instruments/tlc59116ipwr/ic-led-driver-8-bit-tssop-28/dp/3119169 | C, P\*, DK |
| RS | 709-9161 | TLC59116IPWR | TI | TSSOP-28 | — | — | U | https://uk.rs-online.com/web/p/display-drivers/7099161 | C |
| Farnell | 2759860 | PCA9956BTWY | NXP | HTSSOP-38 | P\* £2.69 qty1 | P\* 4,942 (another cache says out of stock / no longer stocked) | U | https://uk.farnell.com/nxp/pca9956btwy/led-driver-constant-current-htssop/dp/2759860 | C, P\* (conflicting) |

Notes:
- LP5012: 12 ch, 35 mA max, 2.7–5.5 V (DK). It is the only candidate here that runs from 2.7 V. PCA9955B is 3–5.5 V (Farnell listing); TLC59116 is 3–5.5 V. Both are fine on a Li-ion rail above 3.0 V.
- The PCA9955B's exposed pad needs hot air or a via-fed thermal pad for hand soldering. The TLC59116IPWR is plain TSSOP-28 at 5–120 mA per channel.
- The RS code 252-0675 from the brief is a TI LM3445MM/NOPB (triac-dimmable driver). It is unrelated, and RS no longer stocks it.

## 2. AVR MCU with UPDI, 16–32 KB, SOIC-20

| Distributor | Order code | MPN | Mfr | Package | Price qty1 / qty10 | Stock / lead | Lifecycle | Source URL | Verified? |
|---|---|---|---|---|---|---|---|---|---|
| Farnell | **not found** | ATtiny1616-SNR | Microchip | SOIC-20W | DK £0.87 / — | DK 0; 1,413 due 11-Nov-2026; 20-wk lead | Active (DK) | — | DK |
| Farnell | **2920834** | ATTINY1616-SFR | Microchip | SOIC-20 (125 °C grade) | P\* £0.781–£0.936 @100+ (two conflicting caches) | stock not shown; page has a "restricted purchase" notice for some accounts | U | (code seen in Farnell result text; URL slug not captured) | C (from listing text), P\* |
| Farnell | 3630321 | ATTINY1616-SF | Microchip | SOIC-20 | — | — | U | https://uk.farnell.com/microchip/attiny1616-sf/microcontrollers-mcu-8-bit/dp/3630321 | C |
| Farnell | **3018703** | ATTINY3216-SN | Microchip | SOIC-20 | P\* £1.04 qty1 (£0.862 @250+) | P\* 647 in stock | DK £0.95 qty1 | https://uk.farnell.com/microchip/attiny3216-sn/mcu-8bit-20mhz-soic-20/dp/3018703 | C, P\*, DK |
| Farnell | 3630440 | ATTINY3216-SNR | Microchip | SOIC-20W | P\* £0.849–£1.02, **full reel only (1,500 MOQ)** | P\* out of stock, 8-wk lead | U | https://uk.farnell.com/microchip/attiny3216-snr/microcontrollers-mcu-8-bit/dp/3630440 | C, P\* |
| Farnell | 2911436 | ATTINY3216-SFR | Microchip | SOIC-20 | — | — | U | https://uk.farnell.com/microchip/attiny3216-sfr/mcu-8bit-avr-20mhz-soic-20/dp/2911436 | C |
| Farnell | 3018697 | ATTINY1614-SSN | Microchip | SOIC-14 | — | — | U | https://uk.farnell.com/microchip/attiny1614-ssn/mcu-8bit-20mhz-soic-14/dp/3018697 | C |
| Farnell | not found | AVR16DD20 / AVR32DD20 (SOIC-20) | Microchip | — | — | — | — | — | not found |
| Farnell | 3872794 | ATTINY3226-SU (tinyAVR 2, SOIC-20) | Microchip | SOIC-20 | — | — | U | https://uk.farnell.com/microchip/attiny3226-su/mcu-8bit-20mhz-soic/dp/3872794 | C. Extra option, not on the brief's list |

CPC does not list ATtiny1616 or ATtiny3216 (search found only ATtiny85 and PICs).

## 3. Li-ion linear charger 4.2 V, SOT-23-5

| Distributor | Order code | MPN | Mfr | Package | Price qty1 / qty10 | Stock / lead | Lifecycle | Source URL | Verified? |
|---|---|---|---|---|---|---|---|---|---|
| Farnell | **1332158** (cut tape), 1332158RL (re-reel) | MCP73831T-2ACI/OT | Microchip | SOT-23-5 | P\* £0.59 qty1, £0.581 @25 | P\* 8,094 in stock + 48,000 incoming. One cache mentions a 100 MOQ; an older (~2019) cache says NLM | DK: Active, 29,784, £0.57 / £0.57, 32-wk lead | https://uk.farnell.com/microchip/mcp73831t-2aci-ot/li-ion-li-poly-charge-controller/dp/1332158 | C, P\* (conflicting), DK |
| Farnell | 1834890 | MCP73831T-2ATI/OT | Microchip | SOT-23-5 | — | — | U | https://uk.farnell.com/microchip/mcp73831t-2ati-ot/batt-charger-li-ion-li-poly-5sot23/dp/1834890 | C |
| CPC | SC18584 | MCP73831T-2ATI/OT | Microchip | SOT-23-5 | P\* ~£0.51 qty1, ~£0.48 @25+ (the same cache also says "pricing unavailable") | — | U | https://cpc.farnell.com/microchip/mcp73831t-2ati-ot/batt-charger-li-ion-li-poly-5sot23/dp/SC18584 | C, P\* |

Both suffixes are 4.2 V / 500 mA. They differ in the preconditioning and termination options, so check the datasheet's option table before swapping one for the other.

## 4. I2C temperature sensor

| Distributor | Order code | MPN | Mfr | Package | Price qty1 / qty10 | Stock / lead | Lifecycle | Source URL | Verified? |
|---|---|---|---|---|---|---|---|---|---|
| Farnell | **not found** | TMP1075DR | TI | SOIC-8 | DK £0.46 / £0.378 | DK 0; 2,500 due 21-Dec-2026 | Active (DK) | — | DK |
| Farnell | not found | TMP1075DGKR | TI | VSSOP-8 | DK £0.46 | — | U | — | DK |
| Farnell | **2841138** (cut tape); 2841138RL; full reel 4384267 | LM75BD,118 | NXP | SOIC-8 | P\* £0.527 @5+, £0.412 @50+ | P\* 47,843 in stock | Active per Farnell; DK £0.64 qty1 | https://uk.farnell.com/nxp/lm75bd-118/temperature-sensor-open-drain/dp/2841138 | C, P\*, DK |
| Farnell | 1854077 | LM75BD,112 | NXP | SOIC-8 | — | — | **No Longer Manufactured** | https://uk.farnell.com/nxp/lm75bd/ic-temp-sensor-digital-8soic/dp/1854077 | C. Avoid |
| Farnell | 2080523 | MCP9808-E/MS | Microchip | MSOP-8 | — | — | U | https://uk.farnell.com/microchip/mcp9808-e-ms/temp-sensor-i2c-20-to-100-deg/dp/2080523 | C |
| Farnell | 3124240 | TMP102AIDRLR | TI | SOT-563 (0.5 mm pitch, awkward to hand-solder) | — | — | U | https://uk.farnell.com/texas-instruments/tmp102aidrlr/temperature-sensor-1deg-c-sot/dp/3124240 | C |
| Farnell | 8455970 | TMP75AIDR | TI | SOIC-8 (LM75 footprint) | — | — | U | https://uk.farnell.com/texas-instruments/tmp75aidr/ic-temperature-sensor-smd-soic8/dp/8455970 | C. Equivalent |
| Farnell | 2396743 | PCT2075D,118 | NXP | SOIC-8 (LM75 drop-in, ±1 °C) | — | — | U | https://uk.farnell.com/nxp/pct2075d-118/temperature-sensor-2deg-cel-soic/dp/2396743 | C. Equivalent |

## 5. P-MOSFET, SOT-23, ≥|20| V, Rds(on) ≤ 60 mΩ @ −2.5 V, |Vgs(th)| ≤ 1 V

| Distributor | Order code | MPN | Mfr | Package | Price qty1 / qty10 | Stock / lead | Lifecycle | Source URL | Verified? |
|---|---|---|---|---|---|---|---|---|---|
| Farnell | **2543533** | DMG2305UX-7 | Diodes | SOT-23 | P\* £0.197 @5+, £0.141 @50+ | P\* 346,272 (cache dated around Oct 2024; the same cache also shows a "no longer stocked" notice) | DK: Active, **0 stock**, backorder, £0.28 / £0.173 | https://uk.farnell.com/diodes-inc/dmg2305ux-7/mosfet-p-ch-20v-sot-23-3/dp/2543533 | C, P\* (conflicting), DK, DS |
| Farnell | **1843688** | DMG3415U-7 | Diodes | SOT-23 | — | — | Datasheet header: **NOT RECOMMENDED FOR NEW DESIGN, use DMP2045U**. DK: 51,820 in stock, £0.39 / £0.238 | https://uk.farnell.com/diodes-inc/dmg3415u-7/mosfet-p-ch-20v-4a-sot-23/dp/1843688 | C, DK, DS |
| Farnell | not checked | DMP2045U-7 | Diodes | SOT-23 | DK £0.33 / £0.202 | DK 54,628 | Active (DK) | — | DK (45 mΩ max @ −4.5 V, Vgs(th) max −1 V; the −2.5 V figure is unverified) |
| Farnell | not checked | PMV48XP,215 | Nexperia | SOT-23 | DK £0.45 qty1 | DK unclear | Active (DK) | — | DK: 55 mΩ @ −4.5 V, **Vgs(th) max −1.25 V, so it fails the ≤1 V criterion** |
| Farnell | 1470106 | SI2323DS-T1-E3 | Vishay | SOT-23 | — | — | **Obsolete** (DK) | https://uk.farnell.com/vishay-siliconix/si2323ds-t1-e3/mosfet-p-20v-4-7a-sot-23/dp/1470106 | C. Avoid |
| Farnell | 1858668 | DMP2305U-7 | Diodes | SOT-23 | — | — | U (listings disagree: 45 vs 60 mΩ) | https://uk.farnell.com/diodes-inc/dmp2305u-7/mosfet-p-ch-20v-4-2a-sot-23/dp/1858668 | C |
| — | not checked | DMP2035U | Diodes | — | — | — | — | — | not checked (search budget ran out) |

Datasheet figures (DS):
- **DMG2305UX**: Rds(on) 52 mΩ typ / **100 mΩ max** @ −2.5 V; 40 / 52 mΩ @ −4.5 V; Vgs(th) −0.5 to −0.9 V. It meets the 60 mΩ target only on the typical value.
- **DMG3415U**: Rds(on) 40 typ / **53 mΩ max** @ −2.5 V; 42.5 mΩ max @ −4.5 V; Vgs(th) −0.3 to −1.0 V. It meets the spec on maximum values, but it is NRND.

## 6. Schottky ≥1 A, ≥20 V, low Vf

| Distributor | Order code | MPN | Mfr | Package | Price qty1 / qty10 | Stock / lead | Lifecycle | Source URL | Verified? |
|---|---|---|---|---|---|---|---|---|---|
| Farnell | 1510673 | PMEG2010AEH,115 (no plain "PMEG2010EH" found) | Nexperia | SOD-123F | P\* £0.459 @5+, £0.284 @10+ | P\* **28 in stock** | DK: Active, 0 stock | https://uk.farnell.com/nexperia/pmeg2010aeh-115/diode-schottky-1a-20v-sod-123f/dp/1510673 | C, P\*, DK |
| Farnell | 1510684 | PMEG3010EH,115 | Nexperia | SOD-123F | P\* £0.352 @5 | P\* out of stock, **54-wk lead** | DK: Active, 0 stock | https://uk.farnell.com/nexperia/pmeg3010eh-115/diode-schottky-1a-30v-sod-123f/dp/1510684 | C, P\*, DK |
| Farnell | 1510687 | PMEG3020EH,115 | Nexperia | SOD-123F | P\* £0.219 @100–499 | — | U | https://uk.farnell.com/nexperia/pmeg3020eh-115/diode-schottky-2a-30v-sod-123f/dp/1510687 | C, P\* |
| Farnell | **1431044** | MBR120VLSFT1G | onsemi | SOD-123FL | P\* £0.354 @5+, £0.208 @50+ (minimum 5) | P\* 6,731 in stock | DK: Active, 108,104, £0.46 / £0.279; Vf 340 mV max @ 1 A | https://uk.farnell.com/on-semiconductor/mbr120vlsft1g/diode-schottky-1a-20v-sod-123fl/dp/1431044 | C, P\*, DK |
| Farnell | 1858617 | B130LAW-7-F | Diodes | SOD-123 | P\* ~£0.398 (2022 cache) | P\* 39,250 (old) | U | https://uk.farnell.com/diodes-inc/b130law-7-f/diode-rec-schot-1a-30v-sod123/dp/1858617 | C, P\* |

## 7. USB-C receptacle (power-only 6-pin preferred)

| Distributor | Order code | MPN | Mfr | Package | Price qty1 / qty10 | Stock / lead | Lifecycle | Source URL | Verified? |
|---|---|---|---|---|---|---|---|---|---|
| Farnell | **3648642** (cut tape); 3648648 = full reel, 1,000 MOQ | USB4125-GF-A | GCT | 6-pos USB-C, R/A, SMT + THT shell, 3 A / 48 V | P\* £0.593 qty1 (cut tape), £0.402 @200+ | P\* 39,682 | DK £0.46 qty1 (status not shown) | https://uk.farnell.com/gct-global-connector-technology/usb4125-gf-a/usb-conn-2-0-type-c-r-a-rcpt-6pos/dp/3648642 | C, P\*, DK |
| Farnell | 3777661 | USB4125-GF-A-0190 | GCT | variant of the above | — | — | U | https://uk.farnell.com/global-connector-technology/usb4125-gf-a-0190/usb-conn-type-c-r-a-rcpt-6pos/dp/3777661 | C |
| Farnell | 3973076 (also seen: 3946920) | USB4135-GF-A | GCT | 6-pos, horizontal | — | — | U | https://uk.farnell.com/gct-global-connector-technology/usb4135-gf-a/usb-conn-type-c-r-a-rcpt-6pos/dp/3973076 | C |
| Farnell | 2924867 | USB4085-GF-A | GCT | 16-pos THT, 5 A (orientation listed inconsistently) | P\* £1.40 qty1 | P\* 54 | U | https://uk.farnell.com/gct-global-connector-technology/usb4085-gf-a/usb-conn-2-0-type-c-r-a-rcpt-16pos/dp/2924867 | C, P\* |
| Farnell | 3367461 | 12401610E4#2A | Amphenol | 24-pos USB 3.1 SMD (fine pitch, poor for hand soldering) | P\* ~£0.86 | — | U | https://uk.farnell.com/amphenol-fci/12401610e4-2a/usb-conn-3-1-type-c-rcpt-smd/dp/3367461 | C |
| — | not checked | Würth 632723300011, Molex 2171750001 | — | — | — | — | — | — | not checked |

## 8. TVS / ESD for 5 V VBUS

| Distributor | Order code | MPN | Mfr | Package | Price qty1 / qty10 | Stock / lead | Lifecycle | Source URL | Verified? |
|---|---|---|---|---|---|---|---|---|---|
| Farnell | **2691565** (also 2691664) | SMF5.0A | Littelfuse | SOD-123FL; uni, 5 V Vrwm, 9.2 V Vc, 200 W | P\* £0.148 @5+ (minimum 5) | P\* ~13–14k | DK £0.37 (single price) | https://uk.farnell.com/littelfuse/smf5-0a/tvs-diode-200w-5v-unidir-sod-123fl/dp/2691565 | C, P\*, DK |
| Farnell | 3361273 | SZSMF5.0AT1G | Littelfuse | SOD-123FL (AEC-Q101) | — | — | U | https://uk.farnell.com/littelfuse/szsmf5-0at1g/tvs-diode-200w-5v-unidir-sod-123fl/dp/3361273 | C |
| Farnell | 1757865 | PESD5V0S1UL,315 | Nexperia | **SOD-882 (1.0 × 0.6 mm DFN), not SOD-323** | — | — | U | https://uk.farnell.com/nexperia/pesd5v0s1ul-315/diode-esd-protection-uni-sod-882/dp/1757865 | C. Unsuitable package |
| — | not checked | ESD9B5.0ST5G, Vishay SMF5V0A | — | — | — | — | — | — | not checked |

## 9. Tactile switch, SMD, top-actuated, 2.5–4.3 mm tall (3 per board)

| Distributor | Order code | MPN | Mfr | Package | Price qty1 / qty10 | Stock / lead | Lifecycle | Source URL | Verified? |
|---|---|---|---|---|---|---|---|---|---|
| Farnell | 3780598 | PTS526 SM15 SMTR2 LFS (Farnell lists "SMTR2"; plain "SMTR" not found) | C&K | 5.2 × 5.2 mm, 160 gf, **1.5 mm actuator height (DK), below the 2.5 mm minimum** | DK £0.12 | DK 250,785 | Active (DK) | (code from Farnell listing text) | C (text), DK |
| Farnell | **3941596** (also 2320087, an older listing at £0.242 @10+) | PTS645SM43SMTR92 LFS | C&K | 6 × 6 mm, 4.3 mm high, 160 gf | P\* £0.192 @10+ (**minimum 10**) | P\* 8,960 | DK £0.27 (status not shown) | https://uk.farnell.com/c-k-components/pts645sm43smtr92-lfs/tactile-switch-0-05a-12vdc-160gf/dp/3941596 | C, P\*, DK |
| — | not checked | TL3301AF160QG, B3FS-1000P, Würth 434121025816 | — | — | — | — | — | — | not checked |

## 10. Slide switch SPDT, right-angle SMD

| Distributor | Order code | MPN | Mfr | Package | Price qty1 / qty10 | Stock / lead | Lifecycle | Source URL | Verified? |
|---|---|---|---|---|---|---|---|---|---|
| Farnell | **9575146** (9575146RL re-reel, £3.50 reel charge) | PCM12SMTR | C&K | SMD, horizontal / side-actuated, 300 mA @ 6 V DC | P\* £0.85 / £0.72 | P\* 26,658 | DK £0.96 (status not shown) | https://uk.farnell.com/c-k-components/pcm12smtr/switch-spdt-0-3a-6vdc-smd/dp/9575146 | C, P\*, DK |
| — | not checked | JS102011SAQN, Würth 450301014042 | — | — | — | — | — | — | not checked |

## 11. JST PH 2-pin battery header

| Distributor | Order code | MPN | Mfr | Package | Price qty1 / qty10 | Stock / lead | Lifecycle | Source URL | Verified? |
|---|---|---|---|---|---|---|---|---|---|
| Farnell | **9492615** | S2B-PH-SM4-TB(LF)(SN) | JST | SMD right-angle (side entry) | P\* £0.478 @10+ (**minimum 10**) | P\* 219,429 | U | https://uk.farnell.com/jst-japan-solderless-terminals/s2b-ph-sm4-tb-lf-sn/connector-header-smt-r-a-2mm-2way/dp/9492615 | C, P\* |
| Farnell | 9491856 | B2B-PH-K-S(LF)(SN) | JST | THT top-entry | — | — | U | https://uk.farnell.com/jst-japan-solderless-terminals/b2b-ph-k-s-lf-sn/header-top-entry-2way-2mm/dp/9491856 | C |
| CPC | CN14073 | B2B-PH-K-S(LF)(SN) | JST | THT top-entry | — | — | U | https://cpc.farnell.com/jst-japan-solderless-terminals/b2b-ph-k-s-lf-sn/header-top-entry-2way-2mm/dp/CN14073 | C |
| CPC | CN14084 | S2B-PH-K-S(LF)(SN) | JST | THT side-entry | — | — | U | https://cpc.farnell.com/jst-japan-solderless-terminals/s2b-ph-k-s-lf-sn/header-side-entry-2way/dp/CN14084 | C |

## 12. JST SH 4-pin (Qwiic / STEMMA QT) header and cable

| Distributor | Order code | MPN | Mfr | Package | Price qty1 / qty10 | Stock / lead | Lifecycle | Source URL | Verified? |
|---|---|---|---|---|---|---|---|---|---|
| Farnell | **1830839** | SM04B-SRSS-TB(LF)(SN) | JST | SMD R/A 1 mm, 4-way | P\* £0.492 @10+, £0.408 @100+ (category page) | P\* 54,298 | U | https://uk.farnell.com/jst-japan-solderless-terminals/sm04b-srss-tb-lf-sn/connector-header-smt-r-a-1mm-4way/dp/1830839 | C, P\* |
| RS | 515-1513 | SM04B-SRSS-TB(LF)(SN) | JST | same | — | — | U | https://uk.rs-online.com/web/p/pcb-headers/5151513 | C |
| RS | **288-4665** | SparkFun KIT-15081 Qwiic Cable Kit (10 cables, 50–500 mm, includes a breadboard-jumper style) | SparkFun | cable kit | P\* £11.09 ex VAT (another cache: £9.63) | — | U | https://uk.rs-online.com/web/p/development-tool-accessories/2884665 | C, P\* |
| Farnell | **1679110** | SHR-04V-S-B (4-way SH housing) | JST | housing | P\* £0.0487 @100+ (**minimum 100, so £4.87**) | P\* 362,052 | U | https://uk.farnell.com/jst-japan-solderless-terminals/shr-04v-s-b/connector-housing-4way/dp/1679110 | C, P\* |
| Farnell | **1679137** | SH3-SH3-28150 (pre-crimped lead, socket to socket, 150 mm, red, 28–32 AWG) | JST | lead | P\* £0.303 @10+ (**minimum 10**) | P\* 8,391 | U | https://uk.farnell.com/jst-japan-solderless-terminals/sh3-sh3-28150/lead-socket-socket-32-28awg-150mm/dp/1679137 | C, P\* |
| Farnell | **1679139** | SH3-SS5-28150 (socket to **free end**, 150 mm, red) | JST | lead | — | — | U | https://uk.farnell.com/jst-japan-solderless-terminals/sh3-ss5-28150/lead-socket-free-end-150mm-red/dp/1679139 | C |
| Farnell | 1679138 | SH 300 mm socket-to-socket lead, red (MPN not captured) | JST | lead | — | — | U | (code from Farnell result text) | C (text) |

No single-cable Adafruit 4210/4401/5384 or SparkFun PRT Qwiic cables turned up at Farnell, RS or CPC. Two ways to get a cable from these distributors:
- **Pre-made:** the RS SparkFun kit above.
- **Built from Farnell parts:** 4 × SH3-SH3-28150 plus 2 × SHR-04V-S-B makes a 150 mm cable. 4 × SH3-SS5-28150 plus 1 × SHR-04V-S-B makes a pigtail with one bare end. Every lead is red, so mark the wires yourself. No crimp tool is needed.

## 13. White LEDs, 2835/3030, CRI ≥ 90, 3 V class, If max ≥ 60 mA, ~2700 K and ~5700–6500 K (8 of each)

| Distributor | Order code | MPN | Mfr | CCT / CRI | If typ / max, Vf | Flux, angle | Price | Stock | Lifecycle | Source URL | Verified? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Farnell | **3498849** | BXEN-27S-11M-3C-00-0-3 (Thrive, SMD 2835, 3.5 × 2.8 × 0.7–0.8 mm) | Bridgelux | 2700 K / **97 typ** | 150 mA test = max; 3.1 V typ | 51 lm @ 150 mA (45 lm @ 85 °C); 116° | P\* £0.10 @5+ … £0.053 @1000+ | P\* 370 | DK: Active (DK has no stock) | https://uk.farnell.com/bridgelux/bxen-27s-11m-3c-00-0-3/cob-led-warm-white-110lm-w-2700k/dp/3498849 | C, P\*, DK |
| Farnell | 3498851 | BXEN-40S-11M-3C-00-0-3 | Bridgelux | 4000 K / 97 | 150 mA; 3.1 V | 56 lm; 116° | — | — | U | https://uk.farnell.com/bridgelux/bxen-40s-11m-3c-00-0-3/cob-led-neutral-white-120lm-w/dp/3498851 | C |
| Farnell | **3498853** | BXEN-50S-11M-3C-00-0-3 | Bridgelux | **5000 K** / 97 | 150 mA; 3.1 V | 59 lm; 116° | P\* £0.175 @5+, £0.116 @100+ | P\* 13,220–37,747 | U | https://uk.farnell.com/bridgelux/bxen-50s-11m-3c-00-0-3/cob-led-cool-white-127lm-w-5000k/dp/3498853 | C, P\* |
| Farnell | not found | BXEN-65S-11M-3C-00-0-3 (6500 K Thrive) | Bridgelux | 6500 K / 97 | 150 mA | 57 lm | DK reel-only (170k) | DK 0 | Active (DK) | — | DK only |
| Farnell | 3227684 | GW QSLM31.QM-H1HV-XX57-1 (OSCONIQ S 3030, quantum dot) | ams OSRAM | 3000 K / **≥90 min** | 65 mA test, 180 mA max; 2.75 V | 43.5 lm; 120° | — | P\* 2,132 (Aug-2023 cache) | U | https://uk.farnell.com/osram-opto-semiconductors/gw-qslm31-qm-h1hv-xx57-1/led-hb-warm-white-43-5lm-3000k/dp/3227684 | C, P\* |
| Farnell | 2470235 / 2470239 | 158563427 (2700 K) / 158563460 (6000 K), WL-SWTP **5630** | Würth | **CRI 85 typ (DK), below 90** | 100 mA test, 300 mA max; 3.0 V | 34 / 39 lm; 120° | P\* £0.402 qty1 (6000 K); DK £0.40 | P\* 4,700 (6000 K) | Active (DK) | https://uk.farnell.com/wurth-elektronik/158563460/led-hb-cool-white-39lm-6000k/dp/2470239 | C, P\*, DK. Fails the CRI requirement |
| Farnell | 4691153 | GW JTLPS1.SM-H5H8-XX38-1-G (DURIS E 2835) | ams OSRAM | 2700 K / CRI not stated | 65 mA; 2.71 V | 120° | — | — | U | https://uk.farnell.com/ams-osram-group/gw-jtlps1-sm-h5h8-xx38-1-g/led-warm-white-2700k-2835-120deg/dp/4691153 | C. CRI unknown |
| RS | 225-0696 | GW QTLTS2.QM-GWH5-XX58-1-65-R33 (OSCONIQ E 2835) | ams OSRAM | 2700 K / ≥90 | 2.71–2.9 V | 120° | — | **unavailable, being discontinued** | NRND/EOL | https://uk.rs-online.com/web/p/leds/2250696 | C |
| RS | 264-8164 | JB2835BWT-G-H40GA0000-N0000001 | Cree LED | 4000 K? / U | — | — | — | — | **Discontinued** | https://uk.rs-online.com/web/p/leds/2648164 | C |
| RS | 232-0718 | L130-2780HA30000B1 (LUXEON 3030 HE Plus) | Lumileds | 2700 K / **80** | 240 mA max; 2.71 V | 30–33.5 lm | — | — | U | https://uk.rs-online.com/web/p/leds/2320718 | C. Fails CRI |
| RS | 137-2002 etc. | NF2W757GT-F1-5080, NF2L757GT-F1-3080/-4080 | Nichia | Ra80 versions only seen | — | — | — | several marked unavailable | U | https://uk.rs-online.com/web/p/leds/1372002 | C. No Ra90 757 found |
| — | not found | Cree JB2835AWT 90 CRI, Samsung LM281B+ / LM302Z+, LUXEON 2835 90 CRI, DURIS S5 PSLR31 white | — | — | — | — | — | — | Farnell's Cree J 2835 parts are flagged NLM. DigiKey's Samsung LM281B listings are mostly Obsolete or reel-only | — | not found |

## 14. RGB LED (separate dies preferred, ≥30 mA per die)

| Distributor | Order code | MPN | Mfr | Package / config | Die If; λd (nm) | Price | Stock | Lifecycle | Source URL | Verified? |
|---|---|---|---|---|---|---|---|---|---|---|
| Farnell | not found | CLV6A-FKB | Cree | — | — | — | — | — | — | not found |
| Farnell | 2414841 | CLP6C-FKB-CKNPRGJBB7A363 | Cree LED | PLCC-6 (separate dies) | 20 mA class per listing (U); 624 / 540 / 480 | — | — | U | https://uk.farnell.com/cree/clp6c-fkb-cknprgjbb7a363/led-red-green-blue-plcc-6/dp/2414841 | C |
| Farnell | 3217313 | CLX6F-FKC-CKNNQDGBB7A363 | Cree LED | PLCC-6 | 15 / 10 / 10 mA test; 624 / 540 / 480 | — | **no longer stocked** | NLS | https://uk.farnell.com/cree-led/clx6f-fkc-cknnqdgbb7a363/full-rank-tape-reel/dp/3217313 | C |
| Farnell | 2981675 | LRTB GVTG (no LRTB GVSR found) | ams OSRAM | MULTILED | 20 mA | — | **no longer stocked** | NLS | https://uk.farnell.com/osram-opto-semiconductors/lrtb-gvtg/led-rgb-1-25cd-3-15cd-630mcd-smd/dp/2981675 | C |
| Farnell | 1827013 | LRTBGFUG | OSRAM | 6-lead MULTILED, 2.8 mm (separate dies) | R 40 / G 50 / B 50 mA | — | — | U | https://uk.farnell.com/osram/lrtbgfug/multiled-black-body-rgb/dp/1827013 | C |
| Farnell | **2322115** (2322115RL re-reel flagged NLM in one cache) | 150141M173100 | Würth | 3528, **common anode** (DK) | 30 mA each (Farnell), 20 mA test (DK); 625 / 520 / 470; 270 / 950 / 230 mcd | P\* £0.53 **inc VAT** qty1 (~£0.44 ex), £0.38 inc @500+; DK £0.37 | P\* 4,731; DK 3,205 | Active (DK) | https://uk.farnell.com/wurth-elektronik/150141m173100/led-1411-rgb-270mcd-950mcd-230mcd/dp/2322115 | C, P\*, DK |
| Farnell | 2401105 | ASMB-MTB0-0A3A2 | Broadcom | PLCC-4 | 20 mA | — | — | **Discontinued / NLM** | https://uk.farnell.com/broadcom/asmb-mtb0-0a3a2/led-hb-rgb-0-09w-plcc-4/dp/2401105 | C |
| Farnell | 2368159 | ASMT-YTB7-0AA02 | Broadcom | PLCC-6 | 20 / 20 / 20 mA (below 30) | — | — | U | https://uk.farnell.com/broadcom/asmt-ytb7-0aa02/led-plcc6-rgb-650-1900-384-mcd/dp/2368159 | C |
| Farnell | 1863244 | ASMT-YTC2-0AA02 | Broadcom | PLCC-6 | R 50 / G 30 / B 30 mA | P\* £1.44 / £0.958 | — | **No Longer Manufactured** | https://uk.farnell.com/broadcom/asmt-ytc2-0aa02/led-plcc6-rgb-full-black-body/dp/1863244 | C |
| Farnell | 1554799 | ASMT-QTB0-0AA02 | Broadcom | PLCC-4 | R 50 / G 30 / B 30 mA | — | — | U | https://uk.farnell.com/broadcom/asmt-qtb0-0aa02/led-plcc4-rgb-black-surface/dp/1554799 | C |
| Farnell | **2335791** | KAAF-5050RGBS-13 (no "AAAF5051" found) | Kingbright | 5050, clear lens (pad config: check datasheet; believed 6-pad separate dies) | R 50 / G 30 / B 30 mA; 625 / 525 / 470; 1.4 cd / 1.4 cd / 420 mcd; Vf 2.5 / 3.3 / 3.5 V | P\* £1.70 @5+ (minimum 5) | P\* 5,189 | U | https://uk.farnell.com/kingbright/kaaf-5050rgbs-13/led-smd-rgb-1400mcd-1400-420/dp/2335791 | C, P\* |
| Farnell | 2112155 | 703-1039 | Multicomp | 5050 RGB | 30 / 30 / 30 mA | — | — | U | https://uk.farnell.com/multicomp/703-1039/led-rgb-5050/dp/2112155 | C |

## 15. Indicator LED and passives (format examples)

| Part | Distributor | Order code | MPN | Notes | Source URL | Verified? |
|---|---|---|---|---|---|---|
| Red LED 0603 | Farnell | 3796306 | MP008277 (Multicomp Pro) | 626 nm, 220 mcd @ 20 mA, 2.4 V | https://uk.farnell.com/multicomp-pro/mp008277/led-red-220mcd-626nm-0603/dp/3796306 | C |
| Red LED 0603 | Farnell | 1716774 | OVS-0608 (Multicomp Pro, also "703-0069") | 625 nm, 300 mcd, 2.1 V | https://uk.farnell.com/multicomp/ovs-0608/led-0603-super-bright-red/dp/1716774 | C |
| 10 k 1 % 0603 | Farnell | 2447230 (cut tape) / 2447230RL / 2446547 (reel) | MCWR06X1002FTL (Multicomp Pro) | MPN pattern `MCWR06X<value code>FTL`, e.g. 100 R = MCWR06X1000FTL, code 2447227 | https://uk.farnell.com/multicomp-pro/mcwr06x1002ftl/res-10k-1-0-1w-0603-thick-film/dp/2447230 | C |
| 10 k 1 % 0603 | Farnell | 9238603 | RC0603FR-0710KL (Yageo) | 100 k = RC0603FR-07100KL, code 9238727 | https://uk.farnell.com/yageo/rc0603fr-0710kl/res-10k-1-0-1w-0603-thick-film/dp/9238603 | C |
| 1 µF 10 V X5R 0603 | Farnell | 3013385 | CL10A105KP8NNNC (Samsung) | — | https://uk.farnell.com/samsung-electro-mechanics/cl10a105kp8nnnc/cap-1uf-10v-mlcc-0603/dp/3013385 | C |
| 4.7 µF 10 V X5R 0603 | Farnell | 3013398 | CL10A475KP8NNNC (Samsung) | — | https://uk.farnell.com/samsung-electro-mechanics/cl10a475kp8nnnc/cap-4-7uf-10v-mlcc-0603/dp/3013398 | C |
| 10 µF 10 V X5R 0603 | Farnell | 3013389 | CL10A106MP8NNNC (Samsung, ±20 %) | The ±10 % "KP8" version was not seen with a code | https://uk.farnell.com/samsung-electro-mechanics/cl10a106mp8nnnc/cap-10uf-10v-mlcc-0603/dp/3013389 | C |
| 10 µF 10 V X5R 0603 | Farnell | 3764144 | 0603X106K100CT (Multicomp Pro, ±10 %) | — | https://uk.farnell.com/multicomp-pro/0603x106k100ct/cap-10uf-10v-mlcc-0603/dp/3764144 | C |
| 100 nF 50 V X7R 0603 | Farnell | 1759122 | MC0603B104K500CT (Multicomp Pro) | P\* ~642k in stock | https://uk.farnell.com/multicomp/mcca000255/mlcc-0603-x7r-50v-100nf/dp/1759122RL | C, P\* |
| 100 nF 50 V X7R 0603 | Farnell | 1362556 | CC0603KRX7R9BB104 (Yageo) | — | https://uk.farnell.com/yageo-phycomp/cc0603krx7r9bb104/cap-mlcc-x7r-100nf-50v-0603/dp/1362556 | C |

Farnell order codes are 7 digits. Re-reel versions add "RL", and a full reel usually has its own separate code. Multiples and minimum quantities vary by line (often 5, 10, 50 or 100) and were not checked line by line.

## 16. Programming adapter (SerialUPDI or native UPDI)

| Distributor | Order code | Product | Price | Source URL | Verified? |
|---|---|---|---|---|---|
| Farnell | 1329311 | FTDI TTL-232R-3V3 (FT232R, 3.3 V I/O, 6-pin SIP, 1.8 m) | P\* £19.41 or £25.85 (two caches) | https://uk.farnell.com/ftdi/ttl-232r-3v3/cable-usb-to-ttl-level-serial/dp/1329311 | C, P\* |
| Farnell | 1740365 | FTDI TTL-232R-3V3-WE (wire-ended) | — | https://uk.farnell.com/ftdi/ttl-232r-3v3-we/cable-usb-ttl-3-3v-wire-end/dp/1740365 | C |
| CPC | SC10142 | FTDI TTL-232R-3V3 | — | https://cpc.farnell.com/ftdi/ttl-232r-3v3/cable-usb-to-ttl-level-seri-converter/dp/SC10142 | C |
| Farnell | 2915518 | Microchip PG164100 MPLAB Snap (supports AVR UPDI through MPLAB X/IPE) | P\* ~£8.24 (looks unusually low; confirm) | https://uk.farnell.com/microchip/pg164100/in-circuit-debugger-1-2v-to-5/dp/2915518 | C, P\* |
| Farnell | 4216621 | Microchip PG164150 MPLAB PICkit 5 | P\* ~£88.83 | https://uk.farnell.com/microchip/pg164150/in-circuit-debugger-2-7v-to-5v/dp/4216621 | C, P\* |
| — | not checked | Adafruit 954 / 5335 | — | — | not checked (search budget ran out) |

---

## Buying from Farnell UK as an individual, and CPC

- **Farnell UK online** has no minimum order quantity or value. Standard delivery is **free at £40 and over**, **£8.99 below £40**, and Express costs £11.99. Items shipped from US (Newark) stock add a flat **£15.95 per order**; an older terms page says £9.99. The terms also reserve a "small order handling charge" on orders below £40 ex VAT. Prices are ex VAT, so a personal buyer adds 20 %. Source: uk.farnell.com/help-delivery-information and the terms-of-purchase page, via search snippets; the live page returned 503.
- **Whether Farnell UK sells to individuals is unverified.** No page in this research said it does or doesn't. Its registration and trade-account pages mention card orders and sole traders.
- **CPC (cpc.farnell.com)** is Farnell's consumer and trade arm. Its registration asks "Business or Personal", so individuals are accepted. Free standard delivery applies on UK mainland orders **over £24.99 ex VAT** (some pages say £20), and Click & Collect is free with no minimum.
- Parts confirmed at CPC: MCP73831T-2ATI/OT SC18584 (~£0.51 ex VAT, against ~£0.59 at Farnell for the -2ACI), FTDI TTL-232R-3V3 SC10142, JST B2B-PH-K-S CN14073, JST S2B-PH-K-S CN14084, and the SparkFun/Pimoroni maker range. Not at CPC: ATtiny1616/3216, the SMD JST S2B-PH-SM4-TB, and most of the specialised LEDs and ICs. CPC prices were checked for only one part, so "cheaper at CPC" is unverified apart from the MCP73831.

## Method and limits

- Farnell, RS and Octopart pages return 403/503 to fetch tools, and no bot-protection workaround was attempted. Farnell and RS data comes from domain-restricted web search. Order codes are reliable because they are in the URLs; prices and stock are cached snippets.
- RS prices were not obtained for any part.
- The web-search budget ran out near the end. These were **not checked**: TMP1075 at RS; Farnell codes for DMP2045U-7, PMV48XP and DMP2035U; ESD9B5.0ST5G and SMF5V0A; TL3301AF160QG, B3FS-1000P and Würth 434121025816; JS102011SAQN and Würth 450301014042; Würth 632723300011 and Molex 2171750001; OSRAM LRTB G6TG; Samsung LM302Z+; Adafruit 954/5335; CPC prices beyond the MCP73831.

---

## Recommended pick per function

1. **LED driver:** Farnell **2759859 PCA9955BTWJ** (HTSSOP-28 with exposed pad, 16 ch, 57 mA). It is the first candidate from the list that Farnell carries; LP5012 is not at Farnell or RS. Confirm the page isn't flagged "no longer stocked" (DigiKey shows it Active with 28k in stock). If it is flagged, use **3119169 TLC59116IPWR** (plain TSSOP-28, ~£1.89, 1,988 in stock). Both need VCC ≥ 3.0 V.
2. **MCU:** Farnell **2920834 ATtiny1616-SFR** if the live page shows stock in small quantities. Otherwise **3018703 ATtiny3216-SN** (SOIC-20, ~£1.04, 647 in stock, same pinout, 32 KB).
3. **Charger:** Farnell **1332158 MCP73831T-2ACI/OT** (~£0.59, ~8k in stock).
4. **Temperature sensor:** Farnell **2841138 LM75BD,118** (SOIC-8, ~£0.53 @5+, ~48k in stock). TMP1075 is not at Farnell.
5. **P-MOSFET:** Farnell **2543533 DMG2305UX-7** is active, but its datasheet Rds(on) at −2.5 V is 52 mΩ typ and **100 mΩ max**. **1843688 DMG3415U-7** meets 53 mΩ max at −2.5 V and Vgs(th) ≤ 1 V, but it is **NRND** (successor DMP2045U, Farnell code not checked). Matt decides whether 60 mΩ is a typ or max limit.
6. **Schottky:** Farnell **1431044 MBR120VLSFT1G** (SOD-123FL, 340 mV max at 1 A, ~£0.35 @5+, 6.7k in stock). The Nexperia PMEG parts are out of stock or on a 54-week lead.
7. **USB-C:** Farnell **3648642 GCT USB4125-GF-A** (6-pin power-only, ~£0.59, ~40k in stock).
8. **TVS:** Farnell **2691565 Littelfuse SMF5.0A** (SOD-123FL, ~£0.15 @5+). PESD5V0S1UL is SOD-882, which is not hand-solderable.
9. **Tactile switch:** Farnell **3941596 C&K PTS645SM43SMTR92 LFS** (6 × 6 × 4.3 mm, minimum 10 at ~£0.19). The PTS526 SM15 is only 1.5 mm tall.
10. **Slide switch:** Farnell **9575146 C&K PCM12SMTR** (~£0.85 / £0.72 @10, 26k in stock).
11. **Battery connector:** Farnell **9492615 JST S2B-PH-SM4-TB(LF)(SN)** (minimum 10 at ~£0.48). For a through-hole part, use **9491856 B2B-PH-K-S**.
12. **Qwiic header and cable:** header Farnell **1830839 SM04B-SRSS-TB(LF)(SN)**. For the cable, either RS **288-4665 SparkFun KIT-15081** (~£11, 10 cables) or build one from Farnell **1679110** SHR-04V-S-B housings with **1679137** (both ends) or **1679139** (one bare end) 150 mm SH leads.
13. **White LEDs:** warm, Farnell **3498849 Bridgelux BXEN-27S-11M-3C-00-0-3** (2700 K, CRI 97, 3.1 V, 150 mA, 51 lm, 116°, ~£0.10; only 370 in stock). Cool, **3498853 BXEN-50S-11M-3C-00-0-3**, but it is **5000 K**, not 5700–6500 K, so this is Matt's call. The 6500 K BXEN-65S is not stocked in the UK, and no CRI ≥ 90 part at 5700–6500 K was found at Farnell or RS.
14. **RGB LED:** separate dies at ≥30 mA, Farnell **2335791 Kingbright KAAF-5050RGBS-13** (R 50 / G 30 / B 30 mA, ~£1.70; confirm the pads are independent in the datasheet). Cheaper but common anode: **2322115 Würth 150141M173100** (3528, 30 mA, ~£0.44 ex VAT).
15. **Passives:** red LED **3796306** MP008277. Resistors: Multicomp Pro MCWR06X…FTL (e.g. **2447230** = 10 k) or Yageo RC0603FR-07… (**9238603**). Capacitors: Samsung CL10A105KP8NNNC **3013385**, CL10A475KP8NNNC **3013398**, CL10A106MP8NNNC **3013389**, and 100 nF MC0603B104K500CT **1759122**.
16. **Programmer:** Farnell **2915518 MPLAB Snap PG164100** (native UPDI, confirm the ~£8 price), or **1329311** (or CPC **SC10142**) FTDI TTL-232R-3V3 for SerialUPDI.
