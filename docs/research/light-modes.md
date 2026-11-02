# Light modes, moon texture data, and lithophane practice: research notes

Product context: a 50 mm 3D-printed lithophane moon, lit from inside by tunable-white LEDs (2700 K and 6500 K, CRI 90) plus an RGB LED.
Prepared 2 Nov 2026.

**How to read this file.**
- Numbers marked **[computed]** were calculated in this session with CIE data. The scripts are in `/tmp/claude-0/-home-user/7ba8e87c-d4ee-5a66-9891-51bde4e0a9a7/scratchpad/scripts/`.
  - The CIE 1931 2° colour-matching functions come from colour-science 0.4.7.
  - The CIE S 026 melanopic and rhodopic action spectra come from the CIE S 026 toolbox v1.049, as bundled in luxpy.
- Numbers marked **[verified]** were read from the source page during this session.
- Numbers marked **[memory]** are from prior knowledge and were not re-verified this session.

> **Coverage gap.** The shared WebSearch budget for this turn (200 calls across all agents) ran out partway through. Section 3 (Thingiverse survey) is therefore **not done**; see §3 for what was checked and the follow-up plan. Sections 1, 2 and 4 used the searches done before the budget ran out, plus direct fetches of known URLs. No search engines were queried by other means, and no bot protection was bypassed.

---

## 1. Light modes

### 1.1 Evidence base

**Brown et al. 2022, PLOS Biology 20(3):e3001571 [verified].** This is the expert consensus, expressed in melanopic EDI (CIE S 026). All values are measured at the eye in the vertical plane, at about 1.2 m height.

| Period | Recommendation (melanopic EDI) |
|---|---|
| Daytime | **≥ 250 lux** minimum. Spectrum ideally "enriched in shorter wavelengths". |
| Evening, starting ≥ 3 h before bed | **≤ 10 lux** maximum. White light should be "depleted in short wavelengths". |
| Night, sleep environment | "as dark as possible"; ambient **≤ 1 lux** maximum. |
| Night, if vision is needed | **≤ 10 lux** maximum. |

Further points from the paper [verified]:
- Common domestic warm-white (2700–3000 K) LEDs already have a melanopic DER "sufficiently low (<0.35…)" to meet the 10 lux evening limit at about 30 lux photopic.
- Ultra-low-melanopic sources "will likely come at the expense of reduced colour discrimination".

**Converting to photopic lux.** melanopic EDI = melanopic DER × photopic lux. So the most photopic lux a mode can deliver is 10 / DER (evening) or 1 / DER (sleep).

**Children.**
- Children show greater melatonin suppression than adults at both 3000 K and 6200 K. The authors recommend low-CCT light at night (Lee et al. 2018, Physiol Rep, PMC6295443) [verified, from a search snippet].
- Glickman et al. 2026 (npj Biological Timing and Sleep 3) measured 25 top-rated children's nightlights across 79 settings [verified, from a search snippet and the USUHS listing].
  - Only 3 of the 25 stayed below 5 lux melanopic EDI at the source, and 2 of those met the adult limit of < 1 lux.
  - "The vast majority do not even meet evening and nighttime recommendations for adults."
  - Their advice is to make nightlights "**dim, red, and far from the bed**".

**Sleep Foundation** (updated 8 Sep 2026; medically reviewed by P. Adavadkar MD) [verified]:
- "A dark room is best for sleep."
- "Red light does not affect circadian rhythms…"
- "Dim yellow and orange colored lights have little impact…"
- It warns that red light that is too bright can still suppress melatonin.
- A Cleveland Clinic specialist (WBRZ news piece) adds that young children may find red scary, so orange or amber is an alternative [verified].
- **AAP:** no official AAP or HealthyChildren.org night-light colour statement was found before the search budget ran out. Do not cite the AAP for colour advice until one is confirmed.

**Dark adaptation [computed].** Rod (rhodopic) DER, where D65 = 1:

| Source | Rhodopic DER |
|---|---|
| 625 nm red | 0.018 |
| 630 nm red | 0.015 |
| 660 nm red | 0.006 |
| 590 nm amber | 0.094 |
| 2700 K | 0.54 |
| 6500 K | 0.99 |

Red at 620–630 nm therefore barely stimulates rods, which is why it preserves dark adaptation. Deep red at 660 nm is better still but looks dimmer per watt.

**Flicker: IEEE 1789-2015** [verified via the DigiKey and DOE summaries]. The IEEE site now lists the standard as "Inactive-Reserved", but it is still the usual reference.

| Level | < 90 Hz | Middle band | No limit above |
|---|---|---|---|
| Low risk: maximum Mod% | 0.025 × f | 0.08 × f, from 90 to 1250 Hz | 1250 Hz |
| No observable effect: maximum Mod% | 0.01 × f | 0.0333 × f, from 90 to 3000 Hz | 3000 Hz |

Firmware recommendation:
- Run the LED PWM at **≥ 3 kHz**, so that 100 % modulation is exempt. Ideally use ≥ 20 kHz to avoid audible coil or MLCC noise and camera banding.
- Use ≥ 12-bit resolution, plus a gamma curve, so that 1–3 % night levels dim smoothly.
- Constant-current analog dimming is an alternative at the lowest levels.

### 1.2 Melanopic DER and maximum lux per mode [computed]

The white values below are for **blackbody** spectra. Real CRI-90 phosphor LEDs usually come out about 5–15 % lower at 2700 K. Brown et al. quote 0.83 for a 6500 K tunable LED. Recompute these with your LED datasheet's SPD.

| Source | mel DER | Max photopic lux for 10 mel-EDI (evening) | Max photopic lux for 1 mel-EDI (sleep) |
|---|---|---|---|
| 1600 K | 0.189 | 53 | 5.3 |
| 1800 K | 0.241 | 42 | 4.2 |
| 2200 K | 0.343 | 29 | 2.9 |
| 2700 K | 0.462 | 22 | 2.2 |
| 3000 K | 0.526 | 19 | 1.9 |
| 4000 K | 0.708 | 14 | 1.4 |
| 5000 K | 0.845 | 12 | 1.2 |
| 6500 K | 0.993 | 10 | 1.0 |
| Red 625 nm (Gaussian, 17 nm FWHM) | 0.0026 | ~3900 | ~390 |
| Amber 590 nm direct emitter | 0.020 | ~500 | ~50 |
| PC-amber (broad) | 0.081 | ~124 | ~12 |
| Green 525 nm | 0.888 | 11 | 1.1 |
| Blue 465 nm | 10.8 | 0.9 | 0.09 |

**Key finding for this LED set (2700 K + 6500 K + RGB) [computed].** A candle or amber colour mixed from **red plus a 525 nm green is not low-melanopic**, because green carries about as much melanopic stimulus per lux as daylight.

| Mix | mel DER |
|---|---|
| R + G "amber" (dominant 590 nm) | 0.40 (direct 590 nm amber: 0.02) |
| 1800 K from 2700 K + R + G (22 / 45 / 33 % luminance) | 0.39 (blackbody: 0.24) |
| 2200 K from 2700 K + R + G (53 / 25 / 21 %) | 0.44 |
| Red + 2700 K only, no green: 70 % red luminance (dominant 612 nm) | 0.14 |
| Red + 2700 K only, no green: 50 % red luminance (605 nm) | 0.23 |
| Red + 2700 K only, no green: 20 % red luminance (≈1870 K, Duv −0.009, slightly pink) | 0.37 |

Conclusions:
- The **night modes should use red, or red plus a little 2700 K, and never green.**
- A genuinely low-blue amber needs a **dedicated 590 nm amber or PC-amber LED**. This is worth considering for the board.
- Candlelight from this LED set mostly wins because it is **dimmer**, not because of its spectrum.

### 1.3 Recommended modes (11), in cycling order from night to day

Notes on the table:
- "Default" is the suggested power-on level for the mode, as a percentage of that mode's maximum.
- The eye-lux target is the illuminance at the user's eye at about 0.5–1 m.
- The modes are in the order a user would cycle through them.

| # | Name | Target | Duv | Default | Purpose | Evidence / notes |
|---|---|---|---|---|---|---|
| 1 | **Night red** | Red LED alone, dominant ≈ 620–625 nm, xy ≈ (0.696, 0.304) | n/a | 2 %, ≤ 0.5–1 lux at pillow | All-night and middle-of-the-night light; preserves dark adaptation | mel DER 0.003, rhodopic DER 0.018. Brown: ≤ 1 lux mel-EDI. Glickman: "dim, red, far from bed". Sleep Foundation: red is the best choice. |
| 2 | **Soft orange / amber night** | Red + 2700 K at about 70 / 30 % luminance, dominant ≈ 610–612 nm. With an amber LED: 590 nm. | n/a | 3 % | Night light for children who dislike red | mel DER 0.14 (dedicated amber: 0.02). Do **not** mix it from R + G (0.40). |
| 3 | **Candlelight** | 1800–1900 K. 1800 K is x 0.5492, y 0.4082. | 0 to +0.002 | 10 % | Wind-down in the last hour before bed | Mixed as 2700 K + R + G, so mel DER ≈ 0.39. Keep ≤ 25 lux at the eye to stay under 10 mel-EDI. |
| 4 | **Warm white** ("yellow / natural white") | 2700 K, x 0.4599, y 0.4106 (the 2700 K channel alone) | 0 | 35 % | Main evening ambient light | mel DER ≈ 0.40–0.46. ≤ 22 lux at the eye in the evening. |
| 5 | **Soft white** | 3000 K, x 0.4369, y 0.4041 (about 87 % 2700 K, 10 % 6500 K, 2.5 % green) | 0 | 50 % | Evening reading | mel DER ≈ 0.53. ≤ 19 lux at the eye in the evening. |
| 6 | **Neutral / reading** | 4000 K, x 0.3805, y 0.3768 (about 53 % 2700 K, 42 % 6500 K, 5 % green) | 0, ANSI nominal +0.001 | 100 % | Daytime reading and task light | mel DER 0.71. Above the evening limit beyond ~14 lux at the eye, so present it as a **day** mode. |
| 7 | **Daylight** | 5000 K, x 0.3451, y 0.3516 (about 28 % 2700 K, 69 % 6500 K, 3.7 % green) | 0 / +0.002 | 100 % | Daytime work and colour checking | mel DER 0.84 |
| 8 | **Cool / blue-white** | 6500 K, x 0.3136, y 0.3237 (the 6500 K channel alone) | 0 / +0.003 | 100 % | Morning and daytime alertness only | mel DER ≈ 0.83–0.99. Brown: daytime ≥ 250 mel-EDI, which the lamp can't reach, so treat it as ambience. Cap it in the evening. |
| 9 | **Moonglow** | ≈ 4100 K (the real colour of moonlight), at a very low level | 0 | 3 % | Decorative "real moon" glow; auto-off timer | Moonlight measures ≈ 4000–4250 K and only *looks* blue (Purkinje shift). Full moon gives ≈ 0.05–0.1 lux, at most ≈ 0.3 lux (Kyba et al. 2017). A blue "moonlight" (≥ 8000 K, mel DER ≥ 1.1) is common in night-light products but wrong for sleep. If offered, keep it decorative and time-limited. |
| 10 | **Green** | RGB green, ≈ 525 nm | n/a | 20 % | Decorative or indicator colour (owner request) | mel DER 0.89, about the same as daylight per lux. Not a night mode. |
| 11 | **Blue** | RGB blue, ≈ 465 nm | n/a | 10 % | Decorative (owner request) | mel DER ≈ 10.8: 1 lux of blue equals about 10 mel-EDI lux, the whole evening budget. Firmware should block or cap it at night. |

Optional extra: **Sunset 2200 K** (x 0.5056, y 0.4152). It gives almost no melanopic benefit over 2700 K with this LED set (0.44 vs 0.46), so merge it into Candlelight unless an amber LED is added.

**Naming caution.** In US lamp marketing, "Soft White" usually means 2700 K and "Warm White" 3000 K, the opposite of the labels used here. Show the CCT in the app or on the label.

**Reading level [memory].** Typical reading recommendations (IES, EN 12464-1) are about 300–500 lux on the page.
- A 50 mm lithophane sphere with an output of tens of lumens will give only tens of lux at 0.4–0.5 m. This is my estimate, not measured.
- So "reading" here means bedside, low-level reading. State that in the product copy.

**Firmware idea.**
- Store a per-mode melanopic DER, measured from the real LEDs and recomputed for each mix.
- Estimate melanopic EDI at a nominal 0.5 m from the drive level.
- In an "evening" time window, cap brightness to ≤ 10 mel-EDI. In a "night" window, cap it to ≤ 1 mel-EDI.

### 1.4 Planckian chromaticities (CIE 1931 2°) for firmware [computed]

The "exact" columns were integrated from the CIE 1931 2° colour-matching functions at 380–780 nm in 1 nm steps, with c₂ = 1.4388 × 10⁻² m·K. They were cross-checked against Kim et al. 2002 (cubic spline) and Krystek 1985 (rational u,v); all agree to within about 0.0006.

| CCT | x (exact) | y (exact) | x (Kim) | y (Kim) | u′ | v′ |
|---|---|---|---|---|---|---|
| 1600 K | 0.5732 | 0.3993 | (outside range) | (outside range) | 0.3451 | 0.5408 |
| **1800 K** | **0.5492** | **0.4082** | 0.5496 | 0.4081 | 0.3231 | 0.5403 |
| 1900 K | 0.5378 | 0.4112 | 0.5381 | 0.4111 | 0.3136 | 0.5396 |
| **2200 K** | **0.5056** | **0.4152** | 0.5054 | 0.4152 | 0.2901 | 0.5360 |
| **2700 K** | **0.4599** | **0.4106** | 0.4593 | 0.4107 | 0.2625 | 0.5274 |
| **3000 K** | **0.4369** | **0.4041** | 0.4366 | 0.4042 | 0.2506 | 0.5214 |
| 3500 K | 0.4053 | 0.3907 | 0.4053 | 0.3909 | 0.2357 | 0.5113 |
| **4000 K** | **0.3805** | **0.3768** | 0.3805 | 0.3767 | 0.2251 | 0.5016 |
| **5000 K** | **0.3451** | **0.3516** | 0.3450 | 0.3516 | 0.2114 | 0.4847 |
| **6500 K** | **0.3136** | **0.3237** | 0.3135 | 0.3237 | 0.2004 | 0.4656 |

- For reference, the CIE daylight-locus points are D50 (0.3457, 0.3586) and D65 (0.3127, 0.3291). Both sit above the Planckian locus.
- Kim et al. 2002 cubic spline, valid for 1667–25000 K:
  - x = −0.2661239e9/T³ − 0.2343589e6/T² + 0.8776956e3/T + 0.179910 for T ≤ 4000 K
  - x = −3.0258469e9/T³ + 2.1070379e6/T² + 0.2226347e3/T + 0.240390 above 4000 K
  - y is then a cubic in x, with coefficient sets for three ranges: up to 2222 K, 2222–4000 K, and above 4000 K. The code is in `colour_calc.py`.

**Mixing 2700 K and 6500 K [computed].** A mix of two whites lies on the straight line between them in xy (and in u′v′). That line passes *below* the Planckian locus, on the magenta/pink side.
- With both endpoints exactly on the locus (Duv 0), the dip is **Duv ≈ −0.0064 at 4000 K**. This is also the deepest point on the line, at about 3900 K, reached with about 51 % of the luminance from the 6500 K channel.
- Other points on the same line:

| CCT | Duv |
|---|---|
| 3000 K | −0.0034 |
| 3500 K | −0.0059 |
| 4500 K | −0.0058 |
| 5000 K | −0.0046 |
| 5700 K | −0.0026 |

- With a typical 6500 K LED at ANSI-nominal Duv +0.003, the dip at 4000 K becomes −0.0049.
- The ANSI C78.377 nominal at 4000 K is +0.001 with a tolerance of ±0.006 [memory], so the uncorrected mix sits at or just outside the tolerance band.
- About 2.5–5 % green, by luminance, brings the mix back onto the locus (see the table in §1.3). This changes mel DER by less than 0.01.
- People often *prefer* a white slightly below the locus (Ohno & Fein 2014, around −0.005 to −0.01 [memory]), so a small residual negative Duv is acceptable. Calibrate against each LED's measured bin chromaticity rather than its nominal value.

---

## 2. Moon texture data: NASA SVS "CGI Moon Kit" (ID 4720)

The page is https://svs.gsfc.nasa.gov/4720. It was first published 6 Sep 2019 and last updated 9 Jan 2026. Visualizer: Ernie Wright (USRA); scientist: Noah Petro (NASA/GSFC).

All files share the base URL `https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/`. Every URL below returned HTTP 200 to a HEAD request; byte counts are the content-length header [verified].

**Projection.**
- The maps use a simple cylindrical (equirectangular) projection with a 2:1 aspect ratio.
- They are "centered on 0° longitude", so the near side is in the middle. The top row is 90° N (TIFF orientation upper-left).

### 2.1 Colour (albedo) maps

**2025 map.** It was built from the LROC WAC Hapke-normalised mosaic, using bands 643, 566 and 415 nm for R, G and B. It preserves more colour and dynamic range than the 2019 map and has more polar detail.

| File | Pixels | Size |
|---|---|---|
| `lroc_color_2k.jpg` | 2048×1024 | 457,942 B |
| `lroc_color_16bit_srgb_4k.tif` | 4096×2048 | 61.9 MB |
| `lroc_color_16bit_srgb_8k.tif` | 8192×4096 | 232 MB |
| `lroc_color_16bit_srgb_16k.tif` | 16384×8192 | 909 MB |
| `lroc_color_16bit_srgb.tif` | full size | 2.4 GB |
| `lroc_color.exr` | full size, float16, linear | 943 MB |

**2019 map.** 24-bit RGB.

| File | Pixels | Size |
|---|---|---|
| `lroc_color_poles_1k.jpg` | 1024×512 | 139,068 B |
| `lroc_color_poles_2k.tif` | 2048×1024 | 3,339,438 B |
| `lroc_color_poles_4k.tif` | 4096×2048 | 13,095,388 B |
| `lroc_color_poles_8k.tif` | 8192×4096 | 48.3 MB |
| `lroc_color_poles_hw5x3.tif` | 9600×3240 | 49.1 MB |
| `lroc_color_poles_16k.tif` | 16384×8192 | 178 MB |
| `lroc_color_poles.tif` | 27360×13680 | 494 MB |

Coverage caveat: the source mosaic covers only 70° N to 70° S. The poles are filled in from the lower-resolution LOLA albedo map (LDAM), which makes up more than 20 % of the pixels but only 6 % of the surface. NASA notes the map is "optimized for aesthetics, not science".

### 2.2 Displacement (elevation) maps, from LOLA gridded data (spring 2019)

Units, as stated on the page:
- **Float TIFFs** are in **kilometres relative to a 1737.4 km sphere**. They are the source half-metre values divided by 2000.
- **uint16 TIFFs** are in **half-metres, offset by +20 000**: h_km = (DN − 20000) / 2000.

The page writes the uint16 reference radius as "1727400 m". That looks like a typo for 1737400 m.

| File | Pixels / resolution | Size |
|---|---|---|
| `ldem_3_8bit.jpg` | 1024×512 (about 2.8 px/°), 8-bit greyscale | 111,552 B |
| `ldem_4.tif` | 1440×720 (4 px/°), float32 km | 4,153,352 B |
| `ldem_4_uint.tif` | 1440×720 (4 px/°), uint16 | 2,076,866 B |
| `ldem_16.tif` | 5760×2880 (16 px/°), float | 66.4 MB |
| `ldem_16_uint.tif` | 5760×2880 (16 px/°), uint16 | 33,201,026 B (31.7 MB) |
| `ldem_hw5x3.tif` | 9600×3240 | 17,149,748 B |
| `ldem_64.tif` | 23040×11520 (64 px/°), float | 1012.6 MB |
| `ldem_64_uint.tif` | 23040×11520 (64 px/°), uint16 | 506 MB |

**Vertical scale [computed].**
- `ldem_4.tif` spans **−8.879 to +10.504 km**, a range of 19.38 km. The uint16 version decodes to the same values to within 1e-6.
- The **8-bit JPEG's scale is not documented** on the page. A regression against `ldem_4.tif` (r = 0.9965) gives **km ≈ 0.0764 × grey − 8.96**. That means grey 0 is about −9.0 km, grey 255 is about +10.5 km, and each grey level is about 76 m. The file's actual grey values run from 5 to 250.

**Scale check for a 50 mm moon [computed].** The full relief range is 1.1 % of the radius, so at 25 mm radius it is only **0.28 mm**, about one layer. True-scale relief is invisible. The lithophane has to map albedo, or exaggerated or high-passed elevation, onto wall thickness.

**Resolution check for a 50 mm moon.** The equator is 157 mm round.
- The 1k map gives 0.15 mm per pixel at the equator, and the 2k map 0.077 mm per pixel.
- `ldem_4` gives 0.11 mm per pixel.
- A 0.4 mm nozzle resolves about 0.4 mm, so the **2k colour map plus `ldem_4` is more than enough**.

### 2.3 Files downloaded

They are in `/tmp/claude-0/-home-user/7ba8e87c-d4ee-5a66-9891-51bde4e0a9a7/scratchpad/research/moon/`. Dimensions were checked with PIL.

| File | Bytes | Pixels | Mode |
|---|---|---|---|
| lroc_color_2k.jpg | 457,942 | 2048×1024 | RGB 8-bit |
| lroc_color_poles_1k.jpg | 139,068 | 1024×512 | RGB 8-bit |
| lroc_color_poles_2k.tif | 3,339,438 | 2048×1024 | RGB 8-bit, LZW |
| ldem_3_8bit.jpg | 111,552 | 1024×512 | L 8-bit |
| ldem_4.tif | 4,153,352 | 1440×720 | float32 (km) |
| ldem_4_uint.tif | 2,076,866 | 1440×720 | uint16 |

### 2.4 Usage terms [verified]

- **SVS FAQ:** "All of our content is in the public domain (unless otherwise noted)… free to download, use, and redistribute for whatever purposes you see fit." The exception is licensed music.
- **Credit line requested on page 4720:** "NASA's Scientific Visualization Studio". The datasets used are LRO LOLA DEM and the LROC WAC colour mosaic (ASU).
- **NASA media guidelines:**
  - NASA content is "generally… not subject to copyright in the United States".
  - "NASA should be acknowledged as the source".
  - Commercial use "must not explicitly or implicitly convey NASA's endorsement".
  - The NASA insignia, logotype and identifiers "are not in the public domain".
  - Commercial use "on merchandise or products" is referred to the Merchandise Guidelines (https://www.nasa.gov/nasa-brand-center/merchandise-approvals/).
- **Recommendation:**
  - Credit the data as "Moon texture: NASA's Scientific Visualization Studio, CGI Moon Kit (LRO LROC/LOLA data)" in the documentation and listing.
  - Use no NASA logo, and don't use the NASA name as branding.
  - If the lamp is sold, read the Merchandise Guidelines page first.

**Related:** SVS 14959, "Moon 3D Models for Web, AR, and Animation" (29 Jan 2026), offers GLB and USDZ models. Examples are `moon_small.glb` (13.2 MB) and `Moon_NASA_LRO_8k_Topo_Small.glb` (77.7 MB).

---

## 3. Thingiverse survey: NOT COMPLETED

**What blocked it.**
- The shared per-turn WebSearch budget (200 calls across all agents) was used up before any `allowed_domains: ["thingiverse.com"]` search ran.
- A single plain `curl` to `https://www.thingiverse.com/` returned **HTTP 403**, a Cloudflare challenge.
- Printables and MakerWorld homepages also returned 403.
- Following the brief, I did not bypass any of this, and I did not query any search engine or site search another way.
- **No thing IDs, titles, authors or licences are listed here**, because none could be verified. I did not want to invent IDs.

**Follow-up plan for a fresh session.**
- Run WebSearch with `allowed_domains: ["thingiverse.com"]` for each of these queries:
  - "moon lamp"
  - "moon lithophane"
  - "lithophane moon lamp LED"
  - "moon lamp 60mm"
  - "small moon lamp"
  - "moon night light"
- For each result, record: thing ID, title, author, licence, diameter, minimum and maximum wall thickness, and the hole diameter or base.
- If the CC licence isn't shown in the snippet, record it as unknown.

**Non-Thingiverse generators, checked directly this session [verified].**
- **3dp.rocks/lithophane** (open source, github.com/MarkDurbin104/3dp.rocks). Defaults from `data/layout.json`:
  - Thickness 3 mm, Thinnest Layer 0.8 mm, Vectors per Pixel 4, Max Size 100 mm, Border 0.
  - Forms: flat, inner/outer curve, cylinder, pillow, dome (image on top or on side), heart. There is **no sphere form**.
  - On commercial use: "Yes, you can use the models to make money or in any commercial setting".
- **lithophanemaker.com** has Sphere and Globe types, plus a "sphere_moon_background" option. Defaults, read from its JS bundle rather than its documentation:
  - Sphere diameter 140 mm; lithophane min/max 0.8 / 2.8 mm.
  - Bottom cylinder 70 mm OD, 4 mm thick, 15 mm high.
  - Optional light base with a 40 mm ID light shaft, a 20×20 mm cable hole, and 45° maximum overhang.
- **ItsLitho** offers a Sphere shape among Plane, Cylinder, Arc, Pumpkin, Vases, Bell and Lamp.

**Lessons for the 50 mm design** (from the generators and guides in §4):
- Common practice is min ≈ 0.8 mm and max ≈ 2.8–3.6 mm, printed fully solid.
- Generator spheres are 100–140 mm with 40–70 mm openings. Scaling one down to 50 mm would leave a 0.3–1 mm wall and a 14–25 mm hole. That supports the team's decision to generate its own geometry at full thickness.

---

## 4. Lithophane print practice

| Parameter | Recommendation | Source |
|---|---|---|
| Min / max thickness, white PLA | **0.8 / 3.0 mm** typical. eSUN PLA+ Cool White 0.8 / 3.0–3.2; SUNLU White 0.8 / 2.8; Tinmorry White 0.8 / 3.6 | ItsLitho filament pages; 3dp.rocks defaults 0.8 / 3.0; lithophanemaker 0.8 / 2.8 [verified] |
| Calibration | Print a calibration (step) test with each filament before the real part, because each has its own "sweet spot" | ItsLitho [verified] |
| Fill | **100 %** infill (ItsLitho uses 99 % to save time), *or* many walls (e.g. 99) with 0 % infill so the lines follow the contours. Bambu: "100% Rectilinear" | ItsLitho; Bambu wiki [verified] |
| Layer height | **0.12 mm** is ItsLitho's sweet spot; 0.2 mm is the coarsest acceptable. Bambu CMYK litho uses a 0.15 mm first layer and a 0.2 mm nozzle | ItsLitho; Bambu wiki [verified] |
| Speed | **30 mm/s** best; 45 mm/s is acceptable | ItsLitho [verified] |
| Orientation | Flat lithophanes print vertical, because XY resolution is better than Z steps. Spheres and globes need supports touching the build plate only: 60° overhang threshold, concentric pattern | ItsLitho [verified] |
| Material | White PLA is the standard (Bambu mono litho: PLA Basic Jade White). **PETG:** min 0.8 mm, layers ≥ 0.16 mm, 250–260 °C, little fan; better outdoors and in heat. Resin: 0.6 / 3.8–4 mm | ItsLitho PETG/resin post (community author) [verified] |
| Heat | Avoid hot light sources: "really powerful LEDs can get pretty hot… especially with PLA". PLA softens at about 55–60 °C [memory], so keep LED power and the thermal path in check inside a sealed 50 mm sphere | Prusa blog [verified] |

**Light transmission and reflectance of white PLA against thickness: no reliable measured data found.**
- I looked for percent transmission at 0.6, 1, 2 and 3 mm, and for reflectance or absorption figures. None turned up before the search budget ran out.
- No Prusa lithophane guide exists in the Prusa help or blog sitemaps; only an LED-lamp post turned up.
- The Bambu wiki has CMYK and backlight-kit pages but no transmission data.
- HueForge's per-filament "Transmission Distance (TD)" is the closest community dataset. It was not retrieved.

**Recommended in-house measurement:**
- Print a step wedge at 0.6, 0.8, 1.0, 1.4, 1.8, 2.2, 2.6, 3.0 and 3.6 mm, using the production filament, layer height and line width.
- Put it over each LED channel (2700 K, 6500 K, R, G, B) in a dark box and measure with a lux meter or spectrometer.
- This gives the transmission curve, and also any colour shift with thickness. White pigment (TiO₂) may warm the light passing through thick areas; this is a hypothesis to test.

---

## Sources

**Circadian, melanopic and light modes**
- Brown TM et al. 2022, "Recommendations for daytime, evening, and nighttime indoor light exposure…", PLOS Biol 20(3):e3001571. https://pmc.ncbi.nlm.nih.gov/articles/PMC8929548/ ; https://doi.org/10.1371/journal.pbio.3001571
- CIE S 026/E:2018 α-opic metrology. Action spectra from the CIE S 026 toolbox v1.049, as bundled in luxpy (https://github.com/ksmet1977/luxpy). Standard DOI 10.25039/S026.2018 [memory].
- colour-science 0.4.7 (CIE 1931 colour-matching functions, Ohno 2013 CCT/Duv). https://www.colour-science.org
- Kim Y-S et al. 2002, J. Korean Phys. Soc. 41(6):865 (cubic-spline Planckian locus). Krystek M. 1985, Color Res. Appl. 10(1):38 [memory, formulas implemented].
- Glickman G et al. 2026, "Quantifying the biological impacts of nightlights…", npj Biol Timing Sleep 3.
  - https://scholar.usuhs.edu/en/publications/quantifying-the-biological-impacts-of-nightlights-implications-fo/
  - https://scholar.usuhs.edu/en/clippings/new-findings-on-science-from-uniformed-services-university-of-the/
  - https://www.brynmawr.edu/news/study-finds-some-nightlights-may-worsen-sleep-quality-children
- Lee S-I et al. 2018, children's melatonin suppression under LED lighting. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6295443/
- Red vs blue LED and melatonin, 2025. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12113466/
- Sleep Foundation:
  - https://www.sleepfoundation.org/bedroom-environment/what-color-light-helps-you-sleep
  - https://www.sleepfoundation.org/bedroom-environment/is-red-light-good-for-sleep
  - https://www.sleepfoundation.org/children-and-sleep/how-blue-light-affects-kids-sleep
- WBRZ / Cleveland Clinic on nightlight colour. https://www.wbrz.com/news/monday-s-health-report-expert-says-night-lights-may-be-keeping-kids-up-instead-of-helping-with-sleep

**Flicker**
- IEEE 1789-2015 (now Inactive-Reserved). https://standards.ieee.org/ieee/1789/4479/
- DigiKey summary of IEEE 1789. https://www.digikey.fi/fi/articles/how-new-flicker-recommendations-will-influence-led-lighting-design
- US DOE. https://www.energy.gov/eere/ssl/articles/flicker-understanding-new-ieee-recommended-practice

**Moonlight**
- Kyba, Mohar & Posch 2017, "How bright is moonlight?", Astron. Geophys. 58(1):1.31. https://fgga.univie.ac.at/en/research/publications/publications-detail-view/pure/a574d8b2-bc2a-441a-96ea-74134b686215/show/publ/Pure
- Wikipedia, Moonlight. https://en.wikipedia.org/wiki/Moonlight
- Moonlight CCT (weak sources):
  - https://www.premiumbeat.com/blog/why-color-grade-moonlight-blue/
  - https://budgetlightforum.com/t/catching-the-light-of-the-moon/53214

**NASA**
- CGI Moon Kit. https://svs.gsfc.nasa.gov/4720
- SVS FAQ. https://svs.gsfc.nasa.gov/help/
- Moon 3D Models. https://svs.gsfc.nasa.gov/14959
- NASA media guidelines. https://www.nasa.gov/nasa-brand-center/images-and-media/ ; Merchandise Guidelines: https://www.nasa.gov/nasa-brand-center/merchandise-approvals/

**Lithophane generators and print guides**
- 3dp.rocks: https://3dp.rocks/lithophane/ (defaults from https://3dp.rocks/lithophane/data/layout.json)
- lithophanemaker.com: https://lithophanemaker.com/
- ItsLitho:
  - Slicer settings: https://itslitho.com/itslitho-blog/slicer-settings-for-lithophanes-tweaking-to-perfection/
  - PETG and resin: https://itslitho.com/itslitho-blog/how-to-3d-print-lithophanes-with-3d-resin-petg/
  - Shapes: https://itslitho.com/itslitho-lithophane-features/
  - Filament pages: https://itslitho.com/product/esun-pla-pro-pla-1-75mm/ ; https://itslitho.com/product/tinmorry-pla-filament-1-75mm-1kg-white/ ; https://itslitho.com/product/sunlu-pla-3d-printer-filament-pla-filament-1-75-mm-dimensional-accuracy-0-02-mm-1-kg-spool-pla-white/
- Bambu wiki, CMYK lithophane: https://wiki.bambulab.com/en/knowledge-sharing/CMYK-color-lithophane-printing-instructions
- Prusa blog, LEDs in prints: https://blog.prusa3d.com/3d-printing-lamps-and-embedding-led-lights_29712/
