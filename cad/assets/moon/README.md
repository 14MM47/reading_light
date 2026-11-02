# Moon texture data

| File | What | Source |
|---|---|---|
| `lroc_color_2k.jpg` | LRO LROC colour (albedo) map, 2048 × 1024, equirectangular, lon −180…180 left→right, lat +90 at the top | NASA Scientific Visualization Studio, *CGI Moon Kit* (SVS 4720), https://svs.gsfc.nasa.gov/4720 |
| `ldem_4.tif` | LOLA elevation, 4 px/degree (1440 × 720), float32 km relative to 1737.4 km radius, same projection | same |

Credit line: *NASA's Scientific Visualization Studio* (data: LRO LROC and LOLA teams). NASA imagery is not copyrighted
(public domain in the US); SVS asks for the credit line above.

`cad/parts/moon_shell.py` turns these into lithophane wall thickness: dark maria and low ground print thicker (darker when lit),
bright highlands and crater rims thinner.
