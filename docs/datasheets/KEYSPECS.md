# KEYSPECS: datasheet facts for schematic/footprint review

Folder: `/tmp/claude-0/-home-user/7ba8e87c-d4ee-5a66-9891-51bde4e0a9a7/scratchpad/ds/` (each PDF has a `pdftotext -layout` `.txt` beside it).
KiCad libs checked: `/usr/share/kicad/footprints` (pad numbers, positions and sizes read from the `.kicad_mod` files).
Convention: KiCad `Device:LED` and `Device:D*` symbols use pin 1 = K and pin 2 = A.
Legend: **OK** means the footprint matches the datasheet. **MISMATCH** or **NOTE** means a reviewer must check it.

---

## 1. Kingbright KAAF-5050RGBS-13 (5050 RGB): NOT RETRIEVED
- I could not get a datasheet from any reachable host:
  - kingbrightusa.com: `/images/catalog/SPEC/KAAF-5050RGBS-13.pdf` returns 404, and the part is missing from their RGB Top-Emitting catalogue.
  - kingbright.com: TLS chain fails via the proxy (curl error 60), and WebFetch returns 503.
  - Mouser, DigiKey, TME and Arrow: Cloudflare "Just a moment" challenge (403).
  - LCSC catalogue search API: Akamai 403.
  - The WebSearch budget was exhausted, so I could not look for mirrors.
- The questions "separate dies?" and the pin map are UNVERIFIED. Do not finalise the footprint or symbol until the PDF is in hand.
- KiCad candidate `LED_SMD:LED_RGB_5050-6`:
  - 6 pads, 1.1 × 2.0 mm, at x = ±2.4 mm and y = −1.7 / 0 / +1.7 mm (pitch 1.7 mm). Pads 1–3 on the left, 4–6 on the right, numbered counter-clockwise.
  - Its descr points to a SparkFun 5060BRG4 datasheet, not Kingbright, so it is unverified for this part.

## 2. Würth 150141M173100: WL-SFTW 3528 full-colour TOP LED, water clear
- File: `we150141m173100.pdf`. Revision 002.011, 2021-12-10, 9 pages.
- Source: https://www.we-online.com/components/products/datasheet/150141M173100.pdf
  - curl got an Akamai 403. The PDF bytes came through the WebFetch tool from the same URL.
- Abs max (p1), at 25 °C:
  - IF 30 mA continuous; IF peak 100 mA (1/10 duty @ 1 kHz).
  - Pdiss: R 72 mW, G 108 mW, B 108 mW.
  - VR 5 V; ESD HBM 1 kV.
  - Operating −40…+85 °C; MSL 3.
- Pinout (p1 schematic): **COMMON ANODE**.
  - Pin 1 = common anode (+).
  - Pin 2 = Blue cathode.
  - Pin 3 = Red cathode.
  - Pin 4 = Green cathode.
  - Polarity mark (chamfered corner) is at **pin 3**, labelled "Cathode; red LED". It is NOT at pin 1.
  - Pads (top view): 3 top-left, 1 top-right, 4 bottom-left, 2 bottom-right.
- Land pattern (p1):
  - Pads 1.5 × 0.9 mm.
  - Outer X 4.6 mm, inner gap 1.6 mm, so the X pitch is 3.1 mm.
  - Y: gap 0.5 mm, overall 2.3 mm, so the Y pitch is 1.4 mm.
- KiCad `LED_SMD:LED_RGB_Wuerth-PLCC4_3.2x2.8mm_150141M173100`: **OK**.
  - Pads 1.5 × 0.9 at (±1.55, ±0.7). Pad 1 at (+1.55, −0.7), 2 at (+1.55, +0.7), 3 at (−1.55, −0.7), 4 at (−1.55, +0.7). This matches exactly.
- Electrical/optical at 20 mA (p2):

  | Colour | VF typ | VF max | Iv min / typ | λdom |
  |---|---|---|---|---|
  | Red | 2.0 V | 2.4 V | 200 / 270 mcd | 625 nm |
  | Green | 3.2 V | 3.6 V | 700 / 950 mcd | 520 nm |
  | Blue | 3.2 V | 3.6 V | 180 / 230 mcd | 470 nm |

  - No VF minimum is given.
  - Viewing angle 120°. IR 10 µA max at 5 V.
- VF–IF curve (p3, typical), read off the graph:
  - At 30 mA: R ≈ 2.12 V, B ≈ 3.27 V, G ≈ 3.40 V.
  - At 20 mA: R ≈ 2.08 V, B ≈ 3.15 V, G ≈ 3.22 V.
  - The curve is dashed above 30 mA.
  - **G/B cannot be regulated at 20–30 mA from a ~3.4 V rail through a current sink.** They need VF plus the driver knee (see TLC59116).

## 3. Bridgelux Thrive SMD 2835 0.5 W 3 V: BXEN-27S-11M-3C-00-0-3 and BXEN-50S-11M-3C-00-0-3
- File: `bridgelux_thrive_2835_0w5_ds312.pdf`. DS312 Rev. E (07/2024), 22 pages.
- Source: https://www.bridgelux.com/sites/default/files/DS312.pdf
- Part number:
  - The trailing `-3` is the colour-bin option: **3-SDCM MacAdam ellipse** (Table 8, p10).
  - `00-0` means the full flux and VF distribution.
  - "S" means Thrive. "11M" means a 1×1 die, mid power.
- Abs max (Table 5, p8):
  - Tj 125 °C; Tsp −40…+105 °C.
  - IF max 150 mA DC; 300 mA peak (≤10 % duty, 10 ms).
  - **No reverse-voltage rating** ("not designed to be driven in reverse").
  - ESD 2 kV HBM; MSL 3; reflow 260 °C for 10 s max.
- Electrical at 150 mA, Tsp 25 °C, pulsed (Table 1 and Table 4):
  - VF 2.90 / 3.13 / 3.30 V (min/typ/max), ±0.15 V tolerance.
  - ΔVF/ΔT −1.04 mV/°C; Rj-sp 31 °C/W.
  - VF bins B/C/D/E cover 2.9–3.3 V in 0.1 V steps.
- Flux at 150 mA, 25 °C (min/typ/max):
  - 2700 K (27S): 45 / 51 / 55 lm, CRI typ 97.
  - 5000 K (50S): 50 / 56 / 65 lm, CRI typ 96.5 (97 at Tsp 55 °C, Table 2).
  - R9 = 92 (Table 3).
- Viewing angle 120° (p13).
- VF at 30 mA (Fig. 9, p12, typical): **≈2.77 V**. Readings: 10 mA ≈ 2.70 V, 50 mA ≈ 2.85 V.
- Relative flux at 30 mA (Fig. 10): ≈20 % of the 150 mA value, so about 10 lm (2700 K) or 11 lm (5000 K).
- Polarity (Fig. 16, p14):
  - The cathode mark is the chamfered corner on the top.
  - The bottom view labels the large pad "−" and the small pad "+". **Large pad = cathode, small pad = anode.**
- Recommended pads (p14):
  - Large 2.07 × 2.1 mm, small 1.17 × 2.1 mm, gap 0.5 mm, overall 3.74 mm.
  - Body 3.5 × 2.8 × 0.7 mm.
- KiCad `LED_SMD:LED_PLCC_2835`: **OK (polarity); pads slightly larger**.
  - Pad 1 (K) is 2.2 × 2.2 at x −0.9. Pad 2 (A) is 1.25 × 2.2 at x +1.375.
  - Gap 0.55 mm, overall 4.0 mm. Datasheet: 3.74 mm overall, gap 0.5 mm.
  - Big pad = pad 1 = K, which agrees with Bridgelux.
  - The footprint descr references a Luckylight R2835 datasheet. The `_Handsoldering` variant has 2.5 / 1.55 mm pads.

## 4. C&K PTS645SM43SMTR92 LFS: 6×6 mm tact switch, SMT
- File: `pts645.pdf`. C&K PTS645 Series, pages B-98…B-102, dated 6 Feb 2018 (p3 footer).
- Source: LCSC mirror for C221880, https://datasheet.lcsc.com/datasheet/pdf/562a3ff7cc4a11dfb85e5324391a4dcf.pdf?productCode=C221880
  - ckswitches.com now redirects to littelfuse.com, which returns an Akamai 403.
- Part number:
  - S = straight (SMT is only available without the ESD pin).
  - M = 160 gf.
  - 43 = 4.3 mm height.
  - SMTR92 = SMT, tape and reel (1,000 per reel).
- Ratings (p1):
  - 50 mA @ 12 VDC.
  - Contact resistance 100 mΩ max; 250 VAC dielectric.
  - 100k operations.
  - **Operating −20…+60 °C**.
- Pinout (p3 "SMT" schematic): SPST-NO.
  - **Pins 1 and 2 are internally connected; pins 3 and 4 are internally connected.** The switch closes (1,2) to (3,4).
  - Layout: 1 top-left, 2 top-right, 3 bottom-left, 4 bottom-right.
- Land pattern (p3): pads 1.55 × 1.3 mm.
  - Outer 9.5 × 5.8 mm, inner 6.4 × 3.2 mm, so the pad centres are at (±3.975, ±2.25).
- KiCad candidates in `Button_Switch_SMD.pretty`:
  - `SW_SPST_PTS645Sx43SMTR92` (the only PTS645 footprint).
  - Others: `SW_SPST_PTS647_Sx38/50/70`, `SW_Tactile_SPST_NO_Straight_CK_PTS636Sx25SMTRLFS`, `SW_Push_1P1T_NO_CK_PTS125Sx*`, `SW_SPST_PTS810`, `SW_Push_1TS009xxxx-xxxx-xxxx_6x6x5mm`.
- KiCad `SW_SPST_PTS645Sx43SMTR92`: **geometry OK, but NUMBERING DIFFERS from the datasheet.**
  - Pads 1.55 × 1.3 at (±3.98, ±2.25).
  - The two top pads are both numbered "1" (datasheet pins 1 and 2). The two bottom pads are both "2" (datasheet pins 3 and 4).
  - This is electrically consistent with a 2-pin `SW_Push` symbol. Do not use a 4-pin symbol with this footprint.

## 5. C&K PCM12SMTR: SPDT slide, right-angle SMT
- File: `pcm12.pdf`. C&K PCM Series, pages I-44/I-45, dated 27 Aug 2019.
- Source: LCSC mirror for C221841, https://datasheet.lcsc.com/datasheet/pdf/677f227074f0d201058521a10a93c772.pdf?productCode=C221841
- Ratings:
  - **0.3 A @ 6 VDC**; contact resistance 70 mΩ max.
  - 10,000 cycles.
  - Operating −10…+85 °C; solder 255 °C max.
  - 3,500 per reel.
- Pinout:
  - Position 1 connects 1–2. Position 2 connects 2–3. **Pin 2 = common.**
  - Pins are NOT evenly spaced: 1→2 is 3.0 mm, 2→3 is 1.5 mm.
- Land (PC mounting, p1):
  - Signal pads 0.7 × 1.5 mm.
  - 2 × NPTH Ø0.9 mm, 3.0 mm apart.
  - 4 shell tabs, 1.0 mm wide, inner span 6.3 mm.
  - Hole centre to signal-pad far edge 2.5 mm, to near edge 1.0 mm.
- KiCad `Button_Switch_SMD:SW_SPDT_PCM12`: **OK**.
  - Pad 1 at x −2.25, pad 2 at +0.75, pad 3 at +2.25 (spacing 3.0 / 1.5), size 0.7 × 1.5.
  - NPTH Ø0.9 at ±1.5. Tabs 1 × 0.8 at ±3.65 (inner span 6.3), unnumbered.

## 6. onsemi MBR120VLSFT1G: Schottky, 20 V / 1 A, SOD-123FL
- File: `mbr120vlsft1.pdf`. MBR120VLSFT1/D Rev. 5, June 2025. Case 498 Issue E (22 Aug 2023).
- Source: https://www.onsemi.com/pdf/datasheet/mbr120vlsft1-d.pdf
- Abs max:
  - VRRM 20 V; IF(AV) 1.0 A (TL 119 °C); IFSM 45 A.
  - TJ −65…+125 °C.
  - RθJA 325 °C/W (minimum pad) or 82 °C/W (700 mm² Cu).
- VF max (p2):

  | IF | 25 °C | 85 °C |
  |---|---|---|
  | 0.1 A | 0.275 V | 0.205 V |
  | **0.5 A** | **0.315 V** | **0.270 V** |
  | 1.0 A | 0.340 V | 0.300 V |

- **IR max 0.60 mA @ 20 V, 25 °C; 15 mA @ 85 °C.** This is high leakage. Matters for a solar blocking diode or reverse-battery use at night or when hot.
- Marking L2V. Polarity: cathode band.
- Pin 1 = cathode (band end), pin 2 = anode.
- Recommended footprint (p6): 2 × 1.25 × 1.22 mm pads, outer span 4.20 mm, so the pitch is 2.95 mm and the inner gap 1.70 mm.
- KiCad `Diode_SMD:D_SOD-123F`: **NOTE: pads smaller than onsemi's**.
  - 1.1 × 1.1 at ±1.4 (pitch 2.8, span 3.9). The inner gap is the same (1.7 mm).
  - Pad 1 = K. Usable, but less heel/toe fillet. Consider 1.25 × 1.22 at ±1.475.

## 7. Littelfuse SMF5.0A: TVS, SOD-123FL. NOT RETRIEVED
- littelfuse.com and m.littelfuse.com return an Akamai 403 to both curl and WebFetch. No legitimate mirror URL was known, and WebSearch was exhausted.
- **All values are unverified; get the PDF before sign-off.** (Littelfuse SMF is 200 W, VR 5.0 V; check VBR, VC and IR from the real table.)
- KiCad trap:
  - The KiCad symbol `Diode:SMF5V0A` defaults to footprint `Diode_SMD:D_SMF`. That is the **Vishay DO-219AB "SMF"** package: 1.3 × 1.4 pads at ±1.45.
  - For the Littelfuse SOD-123FL part, use `D_SOD-123F` and verify it against the Littelfuse land pattern.

## 8. JST PH: S2B-PH-SM4-TB (2 mm pitch, side entry, SMT)
- File: `jst_ph.pdf`. JST PH catalogue extract, 3 pages, PDF modified 2021-02-03.
- Source: LCSC mirror for C295747, https://datasheet.lcsc.com/datasheet/pdf/2474e9261ed7c5f86b55d373e724589d.pdf?productCode=C295747
  - jst-mfg.com returns 403.
- Ratings:
  - 2 A AC/DC (AWG 24); 100 V.
  - −25…+85 °C, including temperature rise.
  - Contact resistance 10 mΩ initial; wire AWG 32–24.
- Header S2B-PH-SM4-TB: A = 2.0 mm, B = 7.9 mm, 1,000 per reel.
- Layout (SM4 side entry, component side, p1):
  - Signal pads 1.0 mm minimum wide at 2.0 mm pitch. They run from ≤5.5 mm to ≥9 mm from the wafer end face, so they are ≥3.5 mm long.
  - Solder-tab pads 1.5 × 3.4 mm, starting 0.2 mm outside the end face (mating side).
  - 1.6 mm from the tab inner edge to the circuit 1 or 2 centre.
  - Circuit 1 is the rightmost when the mating side is at the top.
- KiCad `Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal`: **OK**.
  - Pads 1 and 2 are 1.0 × 3.5 at x = −1 / +1, y −2.85. MP pads are 1.5 × 3.4 at (±3.35, +2.9). Tab-to-pin centre 2.35 mm = 0.75 + 1.6.
  - Edges: 5.5 / 9.0 mm from the end face.
  - Pin 1 is on the left with the mating side at the bottom. That is the same as the JST drawing rotated 180°.

## 9. JST SH: SM04B-SRSS-TB (1 mm pitch, side entry, SMT)
- File: `jst_sh.pdf`. JST eSH, 3 pages, PDF dated 2021-03-24.
- Source: https://www.jst.com/wp-content/uploads/2021/01/eSH-new.pdf
- Ratings:
  - 1.0 A AC/DC (AWG 28); 50 V.
  - −25…+85 °C.
  - Contact resistance 20 mΩ initial; 500 VAC; wire AWG 32–28.
- SM04B-SRSS-TB: A = 3.0 mm, B = 6.0 mm, 3,000 per reel.
- Layout (side entry, viewed from mounting side, p1):
  - Signal pads 0.6 mm wide at 1.0 mm pitch. They lie 4.0 mm to 5.55 mm from the tab outer edge, so they are 1.55 mm long.
  - Tabs 1.2 × 1.8 mm, 0.7 mm from the last pin centre to the tab inner edge.
  - Circuit 1 is on the left (p2 header view).
- KiCad `Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal`: **OK**.
  - Pads 0.6 × 1.55 at x −1.5…+1.5, y −2. MP pads 1.2 × 1.8 at (±2.8, +1.875). Edges 4.0 / 5.55 mm and the 0.7 mm offset both check out.

## 10. Samsung CL10A106KP8NNNC (10 µF/10 V) and CL10A475KO8NNNC (4.7 µF/16 V), X5R 0603
- Files:
  - `samsung_CL10A106KP8NNNC_spec.pdf` (issued May 08 2024) and `samsung_CL10A475KO8NNNC_spec.pdf` (May 09 2024), 38 pages each, spec sheet plus MLCC manual.
  - `samsung_CL10A106KP8NNN_dcbias.json` and `samsung_CL10A475KO8NNN_dcbias.json` hold the DC-bias curves.
- Sources:
  - weblib.samsungsem.com `/mlcc/downloadFile.do` (the site's own Specsheet button: form POST with masterKey and type=specsheet).
  - DC bias from `/graph/mlccEcMakeGraphJson.do` (graphType DCBias, 25 °C).
  - LCSC C19702 and C19666 are the same parts.
- Both parts:
  - 1.60 × 0.80 × 0.80 mm (±0.10); X5R (±15 % over −55…+85 °C); ±10 %.
  - DF 0.1 max; withstand 250 % of rated voltage; Ni/Sn terminations.
- **DC bias, capacitance at 25 °C (Samsung model):**

  | V DC | 0 V | 3.0 V | 3.3 V | 3.7 V | 4.2 V | 5.0 V |
  |---|---|---|---|---|---|---|
  | **10 µF/10 V** | 10.07 µF | 4.84 µF | **4.41 µF (−56 %)** | 4.01 µF | **3.49 µF (−65 %)** | **2.85 µF (−72 %)** |
  | **4.7 µF/16 V** | 4.27 µF | 3.13 µF | 2.97 µF (−30 %) | 2.76 µF | 2.51 µF (−41 %) | **2.14 µF (−50 %)** |

  - The 4.7 µF/16 V part loses less. The MCP73831 needs ≥4.7 µF nominal on both VDD and VBAT.

## 11. 0603 red chip LED: Kingbright APT1608EC (substitute for Multicomp Pro MP008277)
- I could not retrieve MP008277: Farnell returned 503 / bot block. I have not checked that Farnell stocks the Kingbright parts.
- File: `kingbright_apt1608ec.pdf`. V.18A, 02/19/2022.
- Source: https://www.kingbrightusa.com/images/catalog/SPEC/APT1608EC.pdf
- High-efficiency red, GaAsP/GaP, water clear:
  - VF at 20 mA: 2.0 V typ, 2.5 V max (±0.1 V). VF at 30 mA ≈ 2.1 V (p3 curve).
  - Iv 8 / 15 mcd (min/typ) at 20 mA. λdom 617 nm. Viewing angle 150°.
- Abs max: IF 30 mA DC; IFM 160 mA (1/10, 0.1 ms); VR 5 V; PD 75 mW; −40…+85 °C; MSL 3.
- Pinout: **pin 1 = cathode, pin 2 = anode** (symbol on p1). There is a polarity triangle on the bottom.
- Recommended pads: 0.8 × 0.8 mm, gap 0.85 mm (pitch 1.65 mm).
- Alternative file `kingbright_apt1608surck.pdf` (V.22A, 04/08/2023): Hyper Red AlGaInP.
  - VF 1.95 typ / 2.5 max at 20 mA; Iv 120 / 230 mcd; 120°; IF 30 mA max.
- KiCad: the caller listed no 0603 LED footprint. Check `LED_SMD:LED_0603_1608Metric` pad 1 = K.

---

## Parts already in the folder

### TI TLC59116, PW (TSSOP-28)
- File: `tlc59116.pdf`. SLDS157E, Feb 2008, revised Dec 2014, 42 pages. Source URL not recorded (pre-existing).
- Abs max (7.1):
  - VCC 0…7 V; VI −0.4…VCC+0.4 V; VO −0.5…20 V.
  - IO 120 mA per channel; TJ 150 °C; ESD 1.5 kV HBM.
- Recommended (7.3):
  - **VCC 3.0–5.5 V**; VO ≤17 V; IO 5–120 mA.
  - VIH 0.7·VCC; −40…85 °C.
- PW pinout (p4):
  - 1 REXT; 2–5 A0–A3; 6–9 OUT0–3; 10 GND; 11–14 OUT4–7.
  - 15–18 OUT8–11; 19 GND; 20–23 OUT12–15; 24 GND.
  - 25 /RESET (active low); 26 SCL; 27 SDA; 28 VCC.
- I²C:
  - Address `1 1 0 A3 A2 A1 A0` = 0x60–0x6F. 0x68 (All-Call default, D0h) and 0x6B (SWRST, D6h) are reserved, so up to 14 devices fit.
  - **A0–A3 have no internal pull-ups or pull-downs; tie them.** FM+ to 1 MHz.
- Current set: IOUT = (1.26 V / Rext) × 15 × CG (§9.5.9, p20). Examples: 720 Ω gives 26 mA; 360 Ω gives 52 mA (CG 0.992).
- Accuracy: ±8 % absolute, ±6 % channel to channel.
- ICC (VCC 5.5 V, max): 25 mA with outputs off and Rext open, 29 mA at 720 Ω, 37 mA at 180 Ω. **A large quiescent drain for a battery design.** Standby occurs when all outputs are off or /RESET is low.
- **Knee:**
  - Fig. 2 (p9, "Output Current vs Output Voltage") is the only knee data. It shows the outputs saturating at about 0.3 V for 5–20 mA, about 0.45 V at 40 mA, about 0.6 V at 60–80 mA and about 0.7 V at 100–120 mA (eyeballed).
  - The guaranteed test points are VO = 0.6 V at 26 mA and VO = 0.8 V at 52 mA.
  - Regulation is ±0.1 %/V for VO 1–3 V. The text gives no explicit knee figure.
- PW mechanical (p37):
  - Pitch 0.65 mm; body 4.30–4.50 × 9.60–9.80 mm; tip-to-tip 6.20–6.60 mm.
  - Lead 0.19–0.30 mm; foot 0.50–0.75 mm. The PDF has no PW land pattern, only RHB.
- KiCad `Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm`: **OK**. Pads 1.475 × 0.4 at x ±2.8625, 0.65 mm pitch, pin 1 top-left.

### Microchip MCP73831-2ACI/OT (SOT-23-5)
- File: `mcp73831.pdf`. DS20001984H (2005–2020), 29 pages. Source URL not recorded.
- Abs max: VDD 7.0 V; I/O −0.3…VDD+0.3 V; ESD 4 kV HBM.
- Operating: **VDD 3.75–6 V**.
- UVLO: start 3.45 V typ (3.3–3.6), stop 3.38 V typ.
- Supply current: 510 µA typ charging; 53 µA after charge complete.
- Pinout (Table 3-1), SOT-23-5:
  - 1 STAT, 2 VSS, 3 VBAT, 4 VDD, 5 PROG.
  - STAT is tri-state: L while charging, H when complete, Hi-Z when shut down or no battery.
  - 4.7 µF minimum on both VDD and VBAT.
- **"-2AC" option row (Product ID, p26):**
  - VREG 4.20 V (4.168–4.232 V).
  - IPREG/IREG 10 % (7.5–12.5 %).
  - VPTH/VREG 66.5 % (≈2.79 V).
  - ITERM/IREG 7.5 % (5.6–9.4 %).
  - VRTH/VREG 96.5 % (≈4.05 V).
- IREG = 1000 V / RPROG: 2 k gives 505 mA; 10 k gives 100 mA; RPROG range 2–67 kΩ.
- PROG floating or 70–200 kΩ disables charging.
- Pass FET RDS(on) 350 mΩ. θJA 230 °C/W (minimum Cu), 130 °C/W with large Cu.
- Land pattern (DS p24): pitch 0.95 mm, C 2.80 mm, pads 0.60 × 1.10 mm, Z 3.90 mm.
- KiCad `Package_TO_SOT_SMD:SOT-23-5`: **OK numbering**, with a **NOTE** on the land.
  - Pads 1–3 on the left, top to bottom; 4 bottom-right; 5 top-right.
  - Pads are 1.325 × 0.6 at ±1.1375, so C = 2.275 mm (narrower than Microchip's 2.80 mm). Both are fine.

### Microchip ATtiny3216, SOIC-20 (300 mil)
- File: `attiny3216.pdf`. DS40002205A (2020), 588 pages. Source URL not recorded.
- Memory: 32 KB flash; 2 KB SRAM; **256 B EEPROM** (100k cycles).
- Abs max: VDD −0.5…6 V; pin −0.5…VDD+0.5 V; ±40 mA per pin; 200 mA into VDD; RESET pin 13 V.
- VDD 1.8–5.5 V. Clock vs voltage (Table 36-3):
  - 0–5 MHz at 1.8–5.5 V.
  - 0–10 MHz at 2.7–5.5 V.
  - 0–20 MHz at 4.5–5.5 V.
  - Linear between those points, so about 13 MHz is the limit at 3.3 V.
  - BOD typ: 1.8 V (BODLEVEL0), 2.6 V (BODLEVEL2), 4.2 V (BODLEVEL7).
- SOIC-20 pinout (p14):

  | Pin | Name | Pin | Name |
  |---|---|---|---|
  | 1 | VDD | 11 | PB0 |
  | 2 | PA4 | 12 | PC0 |
  | 3 | PA5 (VREFA) | 13 | PC1 |
  | 4 | PA6 | 14 | PC2 |
  | 5 | PA7 | 15 | PC3 |
  | 6 | PB5 | 16 | **PA0 / RESET / UPDI** |
  | 7 | PB4 | 17 | PA1 |
  | 8 | PB3 / TOSC1 | 18 | PA2 |
  | 9 | PB2 / TOSC2 | 19 | PA3 / EXTCLK |
  | 10 | PB1 | 20 | GND |

- **TWI0 (Table 5-1):**
  - Default: SDA = PB1 (pin 10), SCL = PB0 (pin 11).
  - Alternate (`PORTMUX.CTRLB` bit 4 `TWI0` = 1): SDA = PA1 (pin 17), SCL = PA2 (pin 18).
- UPDI: PA0, pin 16. FUSE.SYSCFG0 resets to 0xC4, so RSTPINCFG = 0x1 = UPDI.
- **Measuring VDD:**
  - Set `ADC0.MUXPOS = 0x1D` (INTREF, "internal reference from VREF peripheral").
  - Set `ADC0.CTRLC.REFSEL = 0x1` (VDD), with SAMPCAP = 1 (recommended for references above 1 V).
  - Choose the internal reference with `VREF.CTRLA.ADC0REFSEL`: 0x0 = 0.55 V, 0x1 = 1.1 V, 0x2 = 2.5 V, 0x3 = 4.3 V, 0x4 = 1.5 V.
  - Then VDD = Vref_int × 1023 / ADC result (10-bit).
- Power at 3 V, 25 °C (Tables 36-4 and 36-5):
  - Active: 1.7 mA at 5 MHz; 3.0 mA at 10 MHz.
  - Idle: 0.4 mA at 5 MHz.
  - Standby with RTC on OSCULP32K: 0.71 µA typ, 3 µA max (6 µA at 85 °C).
  - Power-down: 0.1 µA typ, 2 µA max (5 µA at 85 °C).
  - Wake-up from Standby or Power-down: 10 µs typ.
- Land pattern (p569): pitch 1.27 mm, C 9.40 mm, pad 0.60 × 1.95 mm.
- KiCad `Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm`: **OK**. Pads 2.05 × 0.6 at ±4.65 (C = 9.30 mm).

### NXP LM75BD (SO8)
- File: `lm75b.pdf`. Rev. 6.1, 6 Feb 2015, 37 pages. Source URL not recorded.
- Abs max: VCC −0.3…+6.0 V; OS sink 10 mA; Tj 150 °C; ESD 4.5 kV HBM.
- Operating: **VCC 2.8–5.5 V**, −55…+125 °C.
- Pinout: 1 SDA (open-drain), 2 SCL, 3 OS (**open-drain**), 4 GND, 5 A2, 6 A1, 7 A0, 8 VCC.
- Address: `1001 A2 A1 A0` = **0x48–0x4F**. A0–A2, SCL and SDA are not internally biased and must not float.
- OS defaults: comparator mode, **active LOW**, Tos 80 °C, Thyst 75 °C.
- Accuracy and timing:
  - ±2 °C from −25 to +100 °C; ±3 °C from −55 to +125 °C.
  - 0.125 °C resolution (11-bit); converts every 100 ms.
- Current: IDD 100 µA typ, 200 µA max (bus idle); shutdown 0.2 µA typ, 1.0 µA max.
- I²C: 20 Hz–400 kHz with bus time-out. No ESD diodes from SDA/SCL to VCC, so the part does not load the bus when unpowered.
- NXP reflow land (Fig 26): pad 0.60 × 1.30 mm, inner 4.00 mm, outer 6.60 mm, so C = 5.30 mm.
- KiCad `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`: **OK** (numbering standard). Pads 1.95 × 0.6 at ±2.475 (inner 3.0, outer 6.9 mm), so they cover the NXP lands.

### Diodes DMG2305UX-7 (P-MOSFET, SOT23)
- File: `dmg2305ux.pdf`. DS36196 Rev. 8-2, July 2021. Source URL not recorded.
- Abs max:
  - VDSS −20 V; **VGSS ±8 V**.
  - ID −4.2 A (25 °C, steady state), −3.3 A (70 °C); IDM −15 A.
  - PD 1.4 W (1 in² Cu); RθJA 90 °C/W.
- On-state:
  - VGS(th) −0.5…−0.9 V (−250 µA).
  - RDS(on) typ/max: **40 / 52 mΩ at −4.5 V**, **52 / 100 mΩ at −2.5 V**, 68 / 200 mΩ at −1.8 V.
  - Ciss 808 pF; Qg 10.2 nC.
- Pinout (top view, p1): G bottom-left (pin 1), S bottom-right (pin 2), D top (pin 3). Use a **GSD** symbol (`Q_PMOS_GSD`).
- Suggested pads (p5): C 2.0, X 0.8, X1 1.35, Y 0.9, Y1 2.9 mm.
- KiCad `Package_TO_SOT_SMD:SOT-23`: **OK**. Pad 1 at (−0.94, −0.95), 2 at (−0.94, +0.95), 3 at (+0.94, 0), each 1.475 × 0.6.

### GCT USB4125-GF-A (USB-C receptacle, power only, 6P, horizontal top-mount)
- File: `usb4125.pdf`. Drawing date 28 Sep 2020, revision A6, revision date 20/11/25, 2 sheets.
- Source: https://gct.co/files/drawings/usb4125.pdf (byte-identical to the file in the folder).
- Ratings:
  - VBUS 3.0 A total; GND 4.25 A total; A5/B5 1.25 A.
  - 48 VDC; contact resistance 40 mΩ.
  - −30…+85 °C; 20,000 cycles.
  - GF = gold flash; A = tape and reel (1,000). Blank stake suffix = **1.00 mm shell stake** (0190 = 1.90 mm).
- Pads, left to right on the recommended layout: **B12 GND, B9 VBUS, A5 CC1, B5 CC2, A9 VBUS, A12 GND**. SHELL = GND.
  - Mating order: VBUS/GND first, CC second.
  - No D+/D−.
  - The drawing does not specify CC pull-downs. A sink needs 5.1 kΩ Rd on each of CC1 and CC2 (USB-C spec).
- Land:
  - Pad height 1.20 mm.
  - Widths: A5/B5 0.70 mm at ±0.50; A9/B9 0.76 mm at ±1.52; A12/B12 0.80 mm at ±2.75.
  - Shell slots: 4 × drill 0.60 × 1.20 mm, copper 1.10 × 1.70 mm, at x ±4.32 (8.64 mm span).
  - Rows 3.80 mm apart. The front slot centre is 0.68 mm below the signal-pad top edge.
- KiCad `Connector_USB:USB_C_Receptacle_GCT_USB4125-xx-x_6P_TopMnt_Horizontal`: **OK**.
  - A5 at −0.5, B5 at +0.5, B9 at −1.52, A9 at +1.52, B12 at −2.75, A12 at +2.75, all at y −3.08 with the sizes above.
  - Four S1 slots at (±4.32, −3.0) and (±4.32, +0.8).
  - Use this variant, not the `-0190` one (that is the 1.9 mm stake version).
