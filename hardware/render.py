"""Render board layers to PNG for review: python3 hardware/render.py <board> [out_dir]"""
import subprocess
import sys
from pathlib import Path

import cairosvg

HW = Path(__file__).resolve().parent


def render(board, out):
    out.mkdir(parents=True, exist_ok=True)
    pcb = HW / board / f"{board}.kicad_pcb"
    sets = {"top": "F.Cu,F.SilkS,F.Mask,Edge.Cuts,F.Fab", "bottom": "B.Cu,B.SilkS,B.Mask,Edge.Cuts,B.Fab",
            "assembly_top": "F.Fab,F.SilkS,Edge.Cuts,F.CrtYd", "assembly_bottom": "B.Fab,B.SilkS,Edge.Cuts,B.CrtYd"}
    for name, layers in sets.items():
        svg = out / f"{board}_{name}.svg"
        args = ["kicad-cli", "pcb", "export", "svg", "--mode-single", "--layers", layers, "--page-size-mode", "2",
                "--exclude-drawing-sheet", "-o", str(svg), str(pcb)]
        if "bottom" in name:
            args.insert(4, "--mirror")
        subprocess.run(args, capture_output=True)
        cairosvg.svg2png(url=str(svg), write_to=str(out / f"{board}_{name}.png"), output_width=1100,
                         background_color="white")
        svg.unlink()


if __name__ == "__main__":
    render(sys.argv[1], Path(sys.argv[2]) if len(sys.argv) > 2 else HW / sys.argv[1] / "renders")
