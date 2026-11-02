"""Build a .kicad_pcb with pcbnew from the same Part list used for the schematic."""
from __future__ import annotations

import math
import os

import pcbnew

from .schematic import uid

FP_DIR = "/usr/share/kicad/footprints"
MM = pcbnew.FromMM


def V(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


class Board:
    def __init__(self, project: str, rules: dict):
        self.project = project
        self.b = pcbnew.BOARD()
        self.nets: dict[str, pcbnew.NETINFO_ITEM] = {}
        self.fps: dict[str, pcbnew.FOOTPRINT] = {}
        ds = self.b.GetDesignSettings()
        ds.m_TrackMinWidth = MM(rules.get("track_min", 0.2))
        ds.m_ViasMinSize = MM(rules.get("via_min", 0.6))
        ds.m_MinThroughDrill = MM(rules.get("drill_min", 0.3))
        ds.m_ViasMinAnnularWidth = MM(rules.get("annular_min", 0.15))
        ds.m_CopperEdgeClearance = MM(rules.get("edge_clear", 0.3))
        ds.m_HoleToHoleMin = MM(rules.get("hole_to_hole", 0.5))
        ds.m_MinClearance = MM(rules.get("clearance", 0.2))
        ds.m_SolderMaskMinWidth = MM(0.0)
        ds.m_TentViasFront = True           # vias covered by mask (nothing shorts under switches/ICs)
        ds.m_TentViasBack = True
        ns = ds.m_NetSettings
        dflt = ns.GetDefaultNetclass()
        dflt.SetClearance(MM(rules.get("clearance", 0.2)))
        dflt.SetTrackWidth(MM(rules.get("track", 0.25)))
        dflt.SetViaDiameter(MM(rules.get("via", 0.6)))
        dflt.SetViaDrill(MM(rules.get("drill", 0.3)))
        self.b.SetCopperLayerCount(2)

    # ------------------------------------------------------------------ nets
    def net(self, name: str):
        name = self.sch_net(name)
        if name not in self.nets:
            n = pcbnew.NETINFO_ITEM(self.b, name)
            self.b.Add(n)
            self.nets[name] = n
        return self.nets[name]

    def netclass(self, name: str, track: float, clearance: float, via=0.6, drill=0.3, nets=()):
        ds = self.b.GetDesignSettings()
        ns = ds.m_NetSettings
        nc = pcbnew.NETCLASS(name)
        nc.SetTrackWidth(MM(track))
        nc.SetClearance(MM(clearance))
        nc.SetViaDiameter(MM(via))
        nc.SetViaDrill(MM(drill))
        ns.SetNetclass(name, nc)
        for n in nets:
            ns.SetNetclassPatternAssignment(self.sch_net(n), name)

    # ------------------------------------------------------------- footprints
    @staticmethod
    def sch_net(name):
        return name if name.startswith("unconnected-(") or name.startswith("/") else "/" + name

    def place(self, part, x, y, rot=0.0, side="F", pad_map=None):
        lib, name = part.footprint.split(":", 1)
        fp = pcbnew.FootprintLoad(os.path.join(FP_DIR, lib + ".pretty"), name)
        if fp is None:
            raise FileNotFoundError(part.footprint)
        fp.SetReference(part.ref)
        fp.SetValue(part.value)
        fp.SetFPIDAsString(part.footprint)
        fp.SetPath(pcbnew.KIID_PATH("/" + uid(self.project, "sym", part.ref)))
        fp.SetSheetname("Root")
        fp.SetSheetfile(self.project + ".kicad_sch")
        for k, v in part.fields.items():
            if k in ("MPN", "Manufacturer", "Farnell", "LCSC", "PCBWay"):
                fp.SetField(k, str(v))
                f = fp.GetFieldByName(k)
                if f:
                    f.SetVisible(False)
                    f.SetLayer(pcbnew.F_Fab)
        if not part.in_bom:
            fp.SetExcludedFromBOM(True)
        if part.dnp:
            fp.SetDNP(True)
        self.b.Add(fp)
        fp.SetPosition(V(x, y))
        if side == "B":
            fp.Flip(V(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT if hasattr(pcbnew, "FLIP_DIRECTION_LEFT_RIGHT") else False)
        fp.SetOrientationDegrees(rot)
        pad_map = pad_map or {}
        for pad in fp.Pads():
            num = pad.GetNumber()
            pin = pad_map.get(num, num)
            if pin is None or pin == "":
                continue
            if pin.startswith("net:"):
                netname = self.sch_net(pin[4:])
            else:
                if pin not in part.pins:
                    raise KeyError(f"{part.ref}: pad {num} -> pin {pin} not in symbol pin map")
                netname = part.pins[pin]
                if netname is None:
                    from . import symlib
                    pname = next(sp.name for sp in symlib.pins(part.lib_id) if sp.number == pin)
                    netname = f"unconnected-({part.ref}-{pname}-Pad{num})"
                else:
                    netname = self.sch_net(netname)
            pad.SetNet(self.net(netname))
        self.fps[part.ref] = fp
        return fp

    # --------------------------------------------------------------- outline
    def outline_poly(self, pts, width=0.1):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
            s = pcbnew.PCB_SHAPE(self.b)
            s.SetShape(pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(V(x0, y0))
            s.SetEnd(V(x1, y1))
            s.SetLayer(pcbnew.Edge_Cuts)
            s.SetWidth(MM(width))
            self.b.Add(s)

    def outline_circle(self, cx, cy, r, width=0.1):
        s = pcbnew.PCB_SHAPE(self.b)
        s.SetShape(pcbnew.SHAPE_T_CIRCLE)
        s.SetCenter(V(cx, cy))
        s.SetEnd(V(cx + r, cy))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(MM(width))
        self.b.Add(s)

    def slot(self, cx, cy, w, h, r=0.5, width=0.1):
        """Internal cut-out (rounded rectangle) on Edge.Cuts, e.g. a wire pass-through."""
        import math as _m
        pts = []
        for (ox, oy, a0) in ((cx + w / 2 - r, cy - h / 2 + r, -90), (cx + w / 2 - r, cy + h / 2 - r, 0),
                             (cx - w / 2 + r, cy + h / 2 - r, 90), (cx - w / 2 + r, cy - h / 2 + r, 180)):
            for k in range(5):
                a = _m.radians(a0 + 90 * k / 4)
                pts.append((ox + r * _m.cos(a), oy + r * _m.sin(a)))
        self.outline_poly(pts, width)

    def hole(self, x, y, d, pad_d=None, net=None):
        """NPTH (or plated if pad_d given) mounting hole as a one-pad footprint."""
        fp = pcbnew.FOOTPRINT(self.b)
        fp.SetReference(f"H{len([f for f in self.fps if f.startswith('H')]) + 1}")
        fp.SetValue("hole")
        fp.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_BOARD_ONLY)
        pad = pcbnew.PAD(fp)
        if pad_d:
            pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
            pad.SetSize(V(pad_d, pad_d))
            pad.SetLayerSet(pad.PTHMask())
        else:
            pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
            pad.SetSize(V(d, d))
            pad.SetLayerSet(pad.UnplatedHoleMask())
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetDrillSize(V(d, d))
        pad.SetNumber("")
        fp.Add(pad)
        self.b.Add(fp)
        fp.SetPosition(V(x, y))
        if net:
            pad.SetNet(self.net(net))
        self.fps[fp.GetReference()] = fp
        return fp

    # ------------------------------------------------------------------ copper
    def track(self, pts, width, layer, net):
        lay = pcbnew.F_Cu if layer == "F" else pcbnew.B_Cu
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if (x0, y0) == (x1, y1):
                continue
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(V(x0, y0))
            t.SetEnd(V(x1, y1))
            t.SetWidth(MM(width))
            t.SetLayer(lay)
            t.SetNet(self.net(net))
            self.b.Add(t)

    def via(self, x, y, net, d=0.6, drill=0.3):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(V(x, y))
        v.SetWidth(MM(d))
        v.SetDrill(MM(drill))
        v.SetNet(self.net(net))
        self.b.Add(v)
        return v

    def zone(self, net, layer, pts, clearance=0.25, min_width=0.25, priority=0, thermal_gap=0.3, spoke=0.4,
             solid=False):
        z = pcbnew.ZONE(self.b)
        z.SetLayer(pcbnew.F_Cu if layer == "F" else pcbnew.B_Cu)
        if net:
            z.SetNet(self.net(net))
        ol = z.Outline()
        ol.NewOutline()
        for x, y in pts:
            ol.Append(MM(x), MM(y))
        z.SetLocalClearance(MM(clearance))
        z.SetMinThickness(MM(min_width))
        z.SetAssignedPriority(priority)
        z.SetThermalReliefGap(MM(thermal_gap))
        z.SetThermalReliefSpokeWidth(MM(spoke))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if solid else pcbnew.ZONE_CONNECTION_THT_THERMAL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        self.b.Add(z)
        return z

    def keepout(self, layer, pts, tracks=True, vias=True, pour=True):
        z = pcbnew.ZONE(self.b)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(tracks)
        z.SetDoNotAllowVias(vias)
        z.SetDoNotAllowCopperPour(pour)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        ls = pcbnew.LSET()
        for l in layer:
            ls.AddLayer(pcbnew.F_Cu if l == "F" else pcbnew.B_Cu)
        z.SetLayerSet(ls)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in pts:
            ol.Append(MM(x), MM(y))
        self.b.Add(z)
        return z

    def text(self, s, x, y, layer="F.SilkS", size=1.0, thick=0.15, rot=0, mirror=None):
        t = pcbnew.PCB_TEXT(self.b)
        t.SetText(s)
        t.SetPosition(V(x, y))
        lid = {"F.SilkS": pcbnew.F_SilkS, "B.SilkS": pcbnew.B_SilkS, "F.Fab": pcbnew.F_Fab,
               "B.Fab": pcbnew.B_Fab, "F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu}[layer]
        t.SetLayer(lid)
        t.SetTextSize(V(size, size))
        t.SetTextThickness(MM(thick))
        t.SetTextAngleDegrees(rot)
        if mirror if mirror is not None else layer.startswith("B"):
            t.SetMirrored(True)
        self.b.Add(t)

    def place_refs(self, size=0.8, thick=0.13, circle=None):
        """Put each reference designator on silk where it clears pads, other refs and the edge; else Fab only."""
        import itertools
        edge = self.b.GetBoardEdgesBoundingBox()
        pads = []
        for fp in self.b.GetFootprints():
            for p in fp.Pads():
                bb = p.GetBoundingBox()
                pads.append((fp.IsFlipped(), bb))
        placed = []
        # other silk already on the board (footprint graphics and texts, board texts) is an obstacle too
        silk = {pcbnew.F_SilkS: False, pcbnew.B_SilkS: True}
        for fp in self.b.GetFootprints():
            for it in fp.GraphicalItems():
                if it.GetLayer() in silk:
                    bb = it.GetBoundingBox()
                    placed.append(((pcbnew.ToMM(bb.GetX()), pcbnew.ToMM(bb.GetY()), pcbnew.ToMM(bb.GetRight()),
                                    pcbnew.ToMM(bb.GetBottom())), silk[it.GetLayer()]))
        for it in self.b.GetDrawings():
            if it.GetLayer() in silk:
                bb = it.GetBoundingBox()
                placed.append(((pcbnew.ToMM(bb.GetX()), pcbnew.ToMM(bb.GetY()), pcbnew.ToMM(bb.GetRight()),
                                pcbnew.ToMM(bb.GetBottom())), silk[it.GetLayer()]))
            elif it.GetLayer() == pcbnew.Edge_Cuts and it.GetClass() == "PCB_SHAPE" and \
                    it.GetShape() != pcbnew.SHAPE_T_CIRCLE:
                bb = it.GetBoundingBox()                      # internal cut-outs (slots): keep silk 0.3 mm off
                x0, y0, x1, y1 = (pcbnew.ToMM(v) for v in (bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom()))
                if min(x1 - x0, y1 - y0) < 5.0:
                    for side in (False, True):
                        placed.append(((x0 - 0.3, y0 - 0.3, x1 + 0.3, y1 + 0.3), side))
        moved_to_fab = []
        for fp in sorted(self.b.GetFootprints(), key=lambda f: f.GetReference()):
            ref = fp.Reference()
            if fp.GetReference().startswith("H"):
                ref.SetVisible(False)
                continue
            ref.SetTextSize(V(size, size))
            ref.SetTextThickness(MM(thick))
            back = fp.IsFlipped()
            cy = fp.GetCourtyard(pcbnew.B_CrtYd if back else pcbnew.F_CrtYd)
            bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False, False)
            x0, y0, x1, y1 = (pcbnew.ToMM(v) for v in (bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom()))
            cx, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
            # real text size from KiCad's font metrics (its box carries ~0.25 mm of line spacing: take 0.2 off
            # each side so the box is the ink, then keep 0.05 mm of air)
            ref.SetTextAngleDegrees(0)
            rb = ref.GetBoundingBox()
            tw, th = pcbnew.ToMM(rb.GetWidth()) - 0.3, pcbnew.ToMM(rb.GetHeight()) - 0.3
            cands = [(cx, y0 - th / 2 - 0.05, 0), (cx, y1 + th / 2 + 0.05, 0), (x0 - th / 2 - 0.05, cy_, 90),
                     (x1 + th / 2 + 0.05, cy_, 90)]
            # outward first: a reference is read as belonging to the part on its outside, away from the crowd
            bx, by = pcbnew.ToMM(edge.GetCenter().x), pcbnew.ToMM(edge.GetCenter().y)
            cands.sort(key=lambda c: -((c[0] - bx) ** 2 + (c[1] - by) ** 2))
            cands += [(x0 - tw / 2, y0 - th / 2, 0), (x1 + tw / 2, y0 - th / 2, 0),
                      (x0 - tw / 2, y1 + th / 2, 0), (x1 + tw / 2, y1 + th / 2, 0), (cx, cy_, 0)]
            ok = None
            for (tx, ty, ang) in cands:
                w2, h2 = (tw / 2, th / 2) if ang == 0 else (th / 2, tw / 2)
                box = (tx - w2, ty - h2, tx + w2, ty + h2)
                if box[0] < pcbnew.ToMM(edge.GetX()) + 0.3 or box[2] > pcbnew.ToMM(edge.GetRight()) - 0.3 or \
                   box[1] < pcbnew.ToMM(edge.GetY()) + 0.3 or box[3] > pcbnew.ToMM(edge.GetBottom()) - 0.3:
                    continue
                if circle and any((px - circle[0]) ** 2 + (py - circle[1]) ** 2 > circle[2] ** 2
                                  for px in (box[0], box[2]) for py in (box[1], box[3])):
                    continue
                hit = False
                for flipped, pb in pads:
                    if flipped != back:
                        continue
                    px0, py0, px1, py1 = (pcbnew.ToMM(v) for v in (pb.GetX(), pb.GetY(), pb.GetRight(), pb.GetBottom()))
                    if box[0] < px1 + 0.15 and box[2] > px0 - 0.15 and box[1] < py1 + 0.15 and box[3] > py0 - 0.15:
                        hit = True
                        break
                if not hit:
                    for (b2, bk) in placed:
                        if bk == back and box[0] < b2[2] and box[2] > b2[0] and box[1] < b2[3] and box[3] > b2[1]:
                            hit = True
                            break
                if not hit:
                    ok = (tx, ty, ang, box)
                    break
            if ok:
                tx, ty, ang, box = ok
                ref.SetPosition(V(tx, ty))
                ref.SetTextAngleDegrees(ang)
                placed.append((box, back))
            else:
                ref.SetLayer(pcbnew.B_Fab if back else pcbnew.F_Fab)
                moved_to_fab.append(fp.GetReference())
            val = fp.Value()                                  # value on the Fab layer: shows on assembly drawings
            val.SetLayer(pcbnew.B_Fab if back else pcbnew.F_Fab)
            val.SetTextSize(V(0.5, 0.5))
            val.SetTextThickness(MM(0.08))
            val.SetVisible(True)
        return moved_to_fab

    def save(self, path, fill=True):
        """Save, then reload and fill zones (filling an in-memory board built from scratch segfaults)."""
        pcbnew.SaveBoard(path, self.b)
        if fill:
            bb = pcbnew.LoadBoard(path)
            bb.BuildConnectivity()
            pcbnew.ZONE_FILLER(bb).Fill(bb.Zones())
            pcbnew.SaveBoard(path, bb)
