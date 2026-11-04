# 05: Assembly and bring-up

Instructions: **`handoff-05-assembly-bringup.pdf`** (about 3 h for the first lamp).

| Folder / file | Use |
|---|---|
| `drawings/*_assembly_top.pdf`, `*_assembly_bottom.pdf` | 1:1 assembly drawings: references and values on the Fab layer, DNP crossed out |
| `drawings/*-zoomed.png` | The same, zoomed. Easiest to place parts from |
| `schematics/` | Both schematics, for debugging during bring-up |
| `images/lamp-assembly-render.png` | What it looks like assembled |
| `images/fitment/` | How every part fits: exploded pack and head, sections through the pack (buttons, J2) and the head axis |
| `BOM.csv` | What goes where |

Things that are easy to get wrong (all covered in the handoff):
- **LED board:** solder the bottom side first, then the top side in the printed jig.
  - The silk letter beside each white LED says which colour goes there: **W = 2700 K** (D1, D3, D5, D7) and
    **C = 5000 K** (D2, D4, D6, D8).
  - **Würth RGB (D9, at the centre):** the package mark is pin 3, the red cathode. It goes on the silk chamfer,
    which puts the common anode on the "1".
  - **R2 (2.4 kΩ, 0402) is on the top face**, between D1 and D2: the LP5012's EN pull-up. Without it nothing lights.
  - The bottom face's LP5012 is a 0.4 mm-pitch WQFN with an exposed pad: 0.10 mm stencil and a hot plate (or have
    the fab assemble that face).
- **SW1 (slide switch) by iron only.** It is rated 255 °C max.
- **Battery:** meter the polarity, then pass the plug up through the 6.4 × 5.0 mm slot beside J2.
- **Moon base:** jam the cup between the socket nut and a washer + second nut, with the thread cut flush with the
  socket nut before the cable goes in; put a Kapton disc over U1 on the LED board's underside. The moon's skirt slides
  over the cup and turns **clockwise** (seen from the top) 30° to lock; hold the cup band when you turn it.
- **Cable colours:** black GND, red VLED, blue SDA, yellow SCL. They go to the LED-board pads G / V / D / C.
