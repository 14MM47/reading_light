"""Generate project footprints into hardware/lib/reading_light.pretty.

SW_CK_PTS645SM43SMTR92: C&K PTS645 SMD 6x6 mm, 4.3 mm, gull-wing. Pads 1/2 are one contact pair and 3/4 the
other (internally connected pairs) - see docs/datasheets/INDEX.md for the land-pattern source and check.
LED_WirePads_1x04: four 0.9 mm plated holes, 2.0 mm pitch, for soldering the moon cable to the LED board.
"""
from pathlib import Path

OUT = Path(__file__).with_name("reading_light.pretty")

# PTS645 land pattern (C&K PTS645 SMT drawing): terminal centres at x = +/-PAD_X, y = +/-PAD_Y
PTS645 = dict(PAD_X=4.55, PAD_Y=2.25, PAD_W=2.1, PAD_H=1.4, BODY=6.0)


def pts645():
    p = PTS645
    pads = []
    # numbering follows the SW_Push symbol: both top-row terminals = "1", both bottom-row terminals = "2"
    # (each row is one internally connected contact; pressing joins the rows) - VERIFY against the C&K drawing
    for num, (sx, sy) in (("1", (-1, -1)), ("1", (1, -1)), ("2", (-1, 1)), ("2", (1, 1))):
        pads.append(f'\t(pad "{num}" smd roundrect (at {sx * p["PAD_X"]:.3f} {sy * p["PAD_Y"]:.3f}) '
                    f'(size {p["PAD_W"]} {p["PAD_H"]}) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.15))')
    b = p["BODY"] / 2
    cx = p["PAD_X"] + p["PAD_W"] / 2 + 0.25
    cy = b + 0.25
    lines = [
        f'\t(fp_rect (start {-b} {-b}) (end {b} {b}) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))',
        f'\t(fp_circle (center 0 0) (end 1.75 0) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))',
        f'\t(fp_line (start {-b - 0.1} {-1.4}) (end {-b - 0.1} {1.4}) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
        f'\t(fp_line (start {b + 0.1} {-1.4}) (end {b + 0.1} {1.4}) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
        f'\t(fp_line (start {-1.9} {-b - 0.1}) (end {1.9} {-b - 0.1}) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
        f'\t(fp_line (start {-1.9} {b + 0.1}) (end {1.9} {b + 0.1}) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
        f'\t(fp_rect (start {-cx:.2f} {-cy:.2f}) (end {cx:.2f} {cy:.2f}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))',
    ]
    return _fp("SW_CK_PTS645SM43SMTR92", "C&K PTS645 SMD tactile switch 6x6x4.3 mm gull-wing (each pad row is one contact)",
               "switch tactile 6x6 PTS645", lines, pads, ref_y=-b - 1.2, val_y=b + 1.2,
               model="${KICAD9_3DMODEL_DIR}/Button_Switch_SMD.3dshapes/SW_Push_1P1T_NO_E-Switch_TL3301NxxxxxG.step")


def wirepads():
    """Four SMD solder pads for the moon cable (placed on the LED board's bottom face, so nothing reaches the
    LED side). 1.3 x 2.4 mm, 2.0 mm pitch: big enough to tin and tack 26-28 AWG wire."""
    pads = []
    for i in range(4):
        x = -3.0 + 2.0 * i
        pads.append(f'\t(pad "{i + 1}" smd roundrect (at {x:.2f} 0) (size 1.3 2.4) (layers "F.Cu" "F.Mask") '
                    f'(roundrect_rratio 0.15))')
    lines = [
        '\t(fp_rect (start -3.9 -1.45) (end 3.9 1.45) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))',
        '\t(fp_line (start -3.9 1.6) (end -2.1 1.6) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))',
    ]
    return _fp("LED_WirePads_1x04_P2.00mm", "Four SMD solder pads for the moon cable (1 GND, 2 VLED, 3 SDA, 4 SCL)",
               "wire pads", lines, pads, ref_y=-2.2, val_y=2.2, attr="smd")


def _fp(name, descr, tags, lines, pads, ref_y, val_y, attr="smd", model=None):
    s = [f'(footprint "{name}"', '\t(version 20241229)', '\t(generator "kigen")', '\t(layer "F.Cu")',
         f'\t(descr "{descr}")', f'\t(tags "{tags}")',
         f'\t(property "Reference" "REF**" (at 0 {ref_y}) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))',
         f'\t(property "Value" "{name}" (at 0 {val_y}) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))',
         f'\t(attr {attr})']
    s += lines + pads
    if model:
        s.append(f'\t(model "{model}" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
    s.append(")")
    return name, "\n".join(s) + "\n"


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, text in (wirepads(),):   # PTS645: use KiCad's SW_SPST_PTS645Sx43SMTR92 (matches the C&K land pattern)
        (OUT / f"{name}.kicad_mod").write_text(text)
        print("wrote", name)
