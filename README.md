# Moon reading light

A clip-on book light: a slim pack clips to the back cover of a book, a ~12 cm plastic-sleeved metal gooseneck rises
from its top, and a 50 mm 3D-printed lithophane moon at the end glows from LEDs in its base. One slide switch turns
it on and off; a main button cycles ten light modes (CRI-97 tunable whites from 2700 K to 5000 K, 6500 K and a 1900 K candle mixed with the RGB LED, red/orange
night lights, green, blue); up/down buttons set brightness; holding the main button for 2 s saves the current
colour and brightness as the power-on default. USB-C charging, 1200 mAh LiPo.

This repo was produced end to end by Claude Code as a test of the full product-design process
(requirements → research → electronics → layout → firmware → mechanical → verification → BOM/ordering).

| What | Where |
|---|---|
| **Everything to build it, in build order** (PCB files, order lists, print files, firmware hex, drawings, PDFs of every instruction and checklist) | [`deliverable/`](deliverable/): start with `00-START-HERE.pdf` |
| How every part fits (exploded and section views) | [`docs/design/fitment/`](docs/design/fitment/) |
| Requirements, architecture, decisions, status | [`PLAN.md`](PLAN.md) |
| PCB fabrication files (Gerbers zip, BOM, pick-and-place, PDFs, STEP) | [`fab/`](fab/) |
| Printed parts, ready to slice (STL + 3MF) and print settings | [`print/`](print/) |
| Farnell order list and other purchases, assembly cost comparison | [`bom/`](bom/) |
| Firmware (PlatformIO) | [`firmware/`](firmware/) |
| KiCad projects and the generator | [`hardware/`](hardware/) |
| Part models (build123d) and the check pipeline | [`cad/`](cad/) |
| Design calculations, optics, thermal, verification reports | [`docs/`](docs/) |
| Step-by-step handoffs for Claude Code in VS Code (ordering, printing, flashing, bring-up) | [`docs/handoffs/`](docs/handoffs/) |

Moon texture: NASA's Scientific Visualization Studio, CGI Moon Kit (LRO LROC / LOLA data, public domain).
