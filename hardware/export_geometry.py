"""Export board outlines and component body footprints (from the Fab layers) to JSON for the fitment renders.

Run with KiCad's Python (needs pcbnew):  python3 hardware/export_geometry.py <out.json>
Board coordinates in mm, KiCad orientation (y down). For each footprint: ref, footprint name, side, value, and the
points of its Fab-layer body outline (the renderer takes their convex hull and extrudes it to the body height).
"""
import json
import math
import sys
from pathlib import Path

import pcbnew

HW = Path(__file__).resolve().parent
MM = pcbnew.ToMM


def outline(board):
    ps = pcbnew.SHAPE_POLY_SET()
    board.GetBoardPolygonOutlines(ps)
    polys = []
    for i in range(ps.OutlineCount()):
        o = ps.Outline(i)
        holes = [[(MM(ps.Hole(i, h).CPoint(k).x), MM(ps.Hole(i, h).CPoint(k).y))
                  for k in range(ps.Hole(i, h).PointCount())] for h in range(ps.HoleCount(i))]
        polys.append({"outer": [(MM(o.CPoint(k).x), MM(o.CPoint(k).y)) for k in range(o.PointCount())],
                      "holes": holes})
    return polys


def shape_points(s):
    t = s.GetShape()
    if t == pcbnew.SHAPE_T_CIRCLE:
        c, r = s.GetCenter(), s.GetRadius()
        return [(MM(c.x) + MM(r) * math.cos(a), MM(c.y) + MM(r) * math.sin(a))
                for a in [k * math.pi / 8 for k in range(16)]]
    if t == pcbnew.SHAPE_T_POLY:
        pl = s.GetPolyShape()
        return [(MM(pl.Outline(0).CPoint(k).x), MM(pl.Outline(0).CPoint(k).y)) for k in range(pl.Outline(0).PointCount())]
    if t == pcbnew.SHAPE_T_RECT:
        return [(MM(p.x), MM(p.y)) for p in s.GetRectCorners()]
    return [(MM(s.GetStart().x), MM(s.GetStart().y)), (MM(s.GetEnd().x), MM(s.GetEnd().y))]


def footprints(board):
    out = []
    for fp in board.GetFootprints():
        back = fp.IsFlipped()
        fab = pcbnew.B_Fab if back else pcbnew.F_Fab
        pts = []
        for it in fp.GraphicalItems():
            if it.GetLayer() == fab and it.GetClass() == "PCB_SHAPE":
                pts += shape_points(it)
        if len(pts) < 3:                      # no body drawing: fall back to the courtyard
            cy = fp.GetCourtyard(pcbnew.B_CrtYd if back else pcbnew.F_CrtYd)
            if cy.OutlineCount():
                o = cy.Outline(0)
                pts = [(MM(o.CPoint(k).x), MM(o.CPoint(k).y)) for k in range(o.PointCount())]
        pos = fp.GetPosition()
        out.append({"ref": fp.GetReference(), "fp": fp.GetFPIDAsString(), "value": fp.GetValue(),
                    "side": "bottom" if back else "top", "pos": (MM(pos.x), MM(pos.y)),
                    "rot": fp.GetOrientationDegrees(), "body": pts,
                    "pads": [(MM(p.GetPosition().x), MM(p.GetPosition().y)) for p in fp.Pads()]})
    return out


def main(dst):
    data = {}
    for b in ("main-board", "led-board"):
        board = pcbnew.LoadBoard(str(HW / b / f"{b}.kicad_pcb"))
        bb = board.GetBoardEdgesBoundingBox()
        data[b] = {"outline": outline(board), "footprints": footprints(board),
                   "thickness": MM(board.GetDesignSettings().GetBoardThickness()),
                   "bbox": [MM(bb.GetX()), MM(bb.GetY()), MM(bb.GetRight()), MM(bb.GetBottom())]}
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_text(json.dumps(data))
    print("wrote", dst)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "out/fitment/board_geometry.json")
