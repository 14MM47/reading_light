"""Small 2-layer grid router for the reading-light boards.

It reads pads, existing tracks/vias, keepouts and the board outline from a pcbnew BOARD, routes
each requested net with A* over a fine grid (8-way moves per layer, vias between layers) and
writes PCB_TRACK/PCB_VIA objects back. Clearances are enforced with Euclidean distance transforms
plus a raster margin, and KiCad's own DRC is always the final judge (see build scripts).
"""
from __future__ import annotations

import heapq
import math

import numpy as np
import pcbnew
from PIL import Image, ImageDraw
from scipy import ndimage

MM = pcbnew.FromMM
TO = pcbnew.ToMM
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)


class RouteError(RuntimeError):
    pass


class Router:
    def __init__(self, board: pcbnew.BOARD, grid=0.05, clearance=0.2, edge_clear=0.35, via_d=0.6, via_drill=0.3,
                 margin_cells=0.75):
        self.b = board
        self.g = grid
        self.cl = clearance
        self.edge_cl = edge_clear
        self.via_d = via_d
        self.via_drill = via_drill
        self.margin = margin_cells * grid
        bb = board.GetBoardEdgesBoundingBox()
        self.x0 = TO(bb.GetX()) - 1.0
        self.y0 = TO(bb.GetY()) - 1.0
        self.W = int(math.ceil((TO(bb.GetWidth()) + 2.0) / grid))
        self.H = int(math.ceil((TO(bb.GetHeight()) + 2.0) / grid))
        self.netcode = {}
        self.copper = {}          # netname -> bool array [2, H, W]
        self.through = {}         # netname -> bool array [H, W]: cells where vias / plated holes join the layers
        self.smd_pads = {}        # netname -> bool array [2, H, W] (pads only, for via-in-pad avoidance)
        self.blocked_all = np.zeros((2, self.H, self.W), bool)
        self.npth_mask = np.zeros((self.H, self.W), bool)
        self.hole_mask = np.zeros((self.H, self.W), bool)
        self._inside = self._board_inside()
        self.edge_dist = ndimage.distance_transform_edt(self._inside) * grid
        self._scan()

    # ---------------------------------------------------------- rasterising
    def _px(self, x, y):
        return ((x - self.x0) / self.g, (y - self.y0) / self.g)

    def _new_img(self):
        return Image.new("1", (self.W, self.H), 0)

    def _poly_to(self, img, pts):
        d = ImageDraw.Draw(img)
        d.polygon([self._px(x, y) for x, y in pts], fill=1, outline=1)

    def _board_inside(self):
        img = self._new_img()
        d = ImageDraw.Draw(img)
        polys = pcbnew.SHAPE_POLY_SET()
        self.b.GetBoardPolygonOutlines(polys)
        for i in range(polys.OutlineCount()):
            o = polys.Outline(i)
            pts = [(TO(o.CPoint(k).x), TO(o.CPoint(k).y)) for k in range(o.PointCount())]
            d.polygon([self._px(x, y) for x, y in pts], fill=1)
            for h in range(polys.HoleCount(i)):
                hh = polys.Hole(i, h)
                pts = [(TO(hh.CPoint(k).x), TO(hh.CPoint(k).y)) for k in range(hh.PointCount())]
                d.polygon([self._px(x, y) for x, y in pts], fill=0)
        return np.array(img, bool)

    @staticmethod
    def _sps_points(sps):
        out = []
        for i in range(sps.OutlineCount()):
            o = sps.Outline(i)
            out.append([(TO(o.CPoint(k).x), TO(o.CPoint(k).y)) for k in range(o.PointCount())])
        return out

    def _arr(self, net):
        if net not in self.copper:
            self.copper[net] = np.zeros((2, self.H, self.W), bool)
            self.smd_pads[net] = np.zeros((2, self.H, self.W), bool)
            self.through[net] = np.zeros((self.H, self.W), bool)
        return self.copper[net]

    def _scan(self):
        for fp in self.b.GetFootprints():
            for pad in fp.Pads():
                net = pad.GetNetname() or f"__nc_{fp.GetReference()}_{pad.GetNumber()}"
                arr = self._arr(net)
                for li, lay in enumerate(LAYERS):
                    if not pad.IsOnLayer(lay):
                        continue
                    img = self._new_img()
                    for pts in self._sps_points(pad.GetEffectivePolygon(lay, pcbnew.ERROR_INSIDE)):
                        self._poly_to(img, pts)
                    m = np.array(img, bool)
                    arr[li] |= m
                    if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                        self.smd_pads[net][li] |= m
                if pad.HasHole() and pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                    self.through[net] |= arr[0] & arr[1] & self._disc(pad.GetPosition(), TO(pad.GetDrillSize().x) / 2)
                if pad.HasHole():
                    img = self._new_img()
                    d = ImageDraw.Draw(img)
                    c = pad.GetPosition()
                    r = TO(max(pad.GetDrillSize().x, pad.GetDrillSize().y)) / 2
                    cx, cy = self._px(TO(c.x), TO(c.y))
                    d.ellipse([cx - r / self.g, cy - r / self.g, cx + r / self.g, cy + r / self.g], fill=1)
                    self.hole_mask |= np.array(img, bool)
                    if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                        self.blocked_all[:] |= np.array(img, bool)
                        self.npth_mask |= np.array(img, bool)
        for t in self.b.GetTracks():
            self._raster_track(t)
        for z in self.b.Zones():
            if z.GetIsRuleArea() and z.GetDoNotAllowTracks():
                for li, lay in enumerate(LAYERS):
                    if z.IsOnLayer(lay):
                        img = self._new_img()
                        for pts in self._sps_points(z.Outline()):
                            self._poly_to(img, pts)
                        self.blocked_all[li] |= np.array(img, bool)

    def _disc(self, pos, r):
        img = self._new_img()
        d = ImageDraw.Draw(img)
        cx, cy = self._px(TO(pos.x), TO(pos.y))
        rr = max(r / self.g, 0.8)
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=1)
        return np.array(img, bool)

    def _components(self, net):
        """Connected copper groups of a net as a label array [2,H,W]: per-layer labels merged only through
        vias / plated holes (two pads that merely overlap on opposite faces are NOT connected)."""
        own = self.copper[net]
        st = np.ones((3, 3))
        l0, n0 = ndimage.label(own[0], structure=st)
        l1, n1 = ndimage.label(own[1], structure=st)
        parent = list(range(n0 + n1 + 1))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a
        th = self.through[net]
        a = l0[th]
        b = l1[th]
        for x, y in zip(a, b):
            if x and y:
                ra, rb = find(int(x)), find(int(n0 + y))
                if ra != rb:
                    parent[ra] = rb
        lab = np.zeros((2, self.H, self.W), np.int32)
        m0 = l0 > 0
        m1 = l1 > 0
        lab[0][m0] = [find(int(v)) for v in l0[m0]] if m0.any() else []
        lab[1][m1] = [find(int(n0 + v)) for v in l1[m1]] if m1.any() else []
        return lab

    def _raster_seg(self, arr_layer, x0, y0, x1, y1, w):
        img = self._new_img()
        d = ImageDraw.Draw(img)
        r = w / 2 / self.g
        a, b = self._px(x0, y0), self._px(x1, y1)
        d.line([a, b], fill=1, width=max(1, int(round(w / self.g))))
        for (cx, cy) in (a, b):
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=1)
        arr_layer |= np.array(img, bool)

    def _raster_track(self, t):
        net = t.GetNetname()
        arr = self._arr(net)
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            w = TO(t.GetWidth(pcbnew.F_Cu)) if hasattr(t, "GetWidth") else self.via_d
            for li in range(2):
                self._raster_seg(arr[li], TO(p.x), TO(p.y), TO(p.x), TO(p.y), w)
            img = self._new_img()
            d = ImageDraw.Draw(img)
            cx, cy = self._px(TO(p.x), TO(p.y))
            r = self.via_drill / 2 / self.g
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=1)
            self.hole_mask |= np.array(img, bool)
            self.through[net] |= self._disc(p, w / 2)
        else:
            li = 0 if t.GetLayer() == pcbnew.F_Cu else 1
            s, e = t.GetStart(), t.GetEnd()
            self._raster_seg(arr[li], TO(s.x), TO(s.y), TO(e.x), TO(e.y), TO(t.GetWidth()))

    # -------------------------------------------------------------- routing
    def _free_masks(self, net, w, layers):
        """free[li] = cells where a track of width w (centre) may run; freev = legal via centres."""
        others = np.zeros((2, self.H, self.W), bool)
        for n, a in self.copper.items():
            if n != net:
                others |= a
        free = np.zeros((2, self.H, self.W), bool)
        freev = np.ones((self.H, self.W), bool)
        need_t = self.cl + w / 2 + self.margin
        need_v = self.cl + self.via_d / 2 + self.margin
        def edt(mask):                            # distance (mm) to the nearest set cell; inf if none is set
            return ndimage.distance_transform_edt(~mask) * self.g if mask.any() else np.full(mask.shape, np.inf)
        npth_d = edt(self.npth_mask)
        for li in range(2):
            dist = ndimage.distance_transform_edt(~others[li]) * self.g
            ok_edge_t = self.edge_dist > (self.edge_cl + w / 2 + self.margin)
            # keep the whole track / via body (not only its centre line) out of rule areas, and clear NPTH holes
            blk = edt(self.blocked_all[li])
            free[li] = (dist > need_t) & ok_edge_t & (blk > w / 2 + self.margin) & (npth_d > need_t)
            if li not in layers:
                free[li] = False
            freev &= (dist > need_v) & (blk > self.via_d / 2 + self.margin) & (npth_d > need_v)
        holed = ndimage.distance_transform_edt(~self.hole_mask) * self.g
        freev &= holed > (0.5 + self.via_drill / 2 + self.via_drill / 2 + self.margin)
        freev &= self.edge_dist > (self.edge_cl + self.via_d / 2 + self.margin)
        own_smd = self.smd_pads.get(net)
        if own_smd is not None:
            near_pad = ndimage.distance_transform_edt(~(own_smd[0] | own_smd[1])) * self.g
            freev &= near_pad > (self.via_d / 2 + 0.1)
        if len(layers) < 2:
            freev[:] = False
        return free, freev

    def route_net(self, net, width, layers=(0, 1), via_cost_mm=1.6, layer_cost=(1.0, 1.6), max_expand=3_000_000):
        if net not in self.copper and "/" + net in self.copper:
            net = "/" + net
        if net not in self.copper:
            raise RouteError(f"net {net} has no copper")
        own = self.copper[net]
        lab = self._components(net)
        comps = sorted(set(np.unique(lab)) - {0})
        if len(comps) <= 1:
            return []
        free, freev = self._free_masks(net, width, layers)
        for li in range(2):
            if li in layers:
                free[li] |= own[li]
        sizes = {c: int((lab == c).sum()) for c in comps}
        tree_label = max(comps, key=lambda c: sizes[c])
        tree = (lab == tree_label)                       # [2,H,W]
        remaining = [c for c in comps if c != tree_label]
        new_items = []
        while remaining:
            dt = ndimage.distance_transform_edt(~(tree[0] | tree[1])) * self.g
            best = min(remaining, key=lambda c: dt[(lab == c).any(0)].min())
            src3 = (lab == best)
            path = self._astar3(src3, tree & own, free, freev, via_cost_mm, layer_cost, max_expand)
            if path is None:
                raise RouteError(f"could not connect a part of net {net}")
            items = self._commit(net, width, path)
            new_items += items
            tree |= src3
            for (li, i, j) in path:
                tree[li, i, j] = True
            remaining.remove(best)
        return new_items

    def _astar3(self, src3, target, free, freev, via_cost_mm, layer_cost, max_expand):
        """A* from a 3-D start set (layer-specific) to a 3-D target set."""
        return self._astar(src3[0] | src3[1], src3, target, free, freev, via_cost_mm, layer_cost, max_expand,
                           exclude=src3)

    def _astar(self, src, own, target, free, freev, via_cost_mm, layer_cost, max_expand, exclude=None):
        """src: 2-D start mask; own: [2,H,W] start-layer copper; target: [2,H,W] goal cells per layer."""
        H, W, g = self.H, self.W, self.g
        tgt_any = target[0] | target[1]
        hdist = ndimage.distance_transform_edt(~tgt_any) * g
        openh = []
        best = {}
        came = {}
        starts = []
        for li in range(2):
            ii, jj = np.nonzero(src & own[li] & free[li])
            for i, j in zip(ii, jj):
                starts.append((li, int(i), int(j)))
        if not starts:
            return None
        for s in starts:
            best[s] = 0.0
            heapq.heappush(openh, (hdist[s[1], s[2]], 0.0, s))
        moves = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
                 (-1, -1, math.sqrt(2)), (-1, 1, math.sqrt(2)), (1, -1, math.sqrt(2)), (1, 1, math.sqrt(2))]
        vc = via_cost_mm
        n = 0
        while openh:
            f, gc, cur = heapq.heappop(openh)
            if gc > best.get(cur, 1e18) + 1e-9:
                continue
            li, i, j = cur
            if target[li, i, j] and not (exclude[li, i, j] if exclude is not None else src[i, j]):
                path = [cur]
                while cur in came:
                    cur = came[cur]
                    path.append(cur)
                return path[::-1]
            n += 1
            if n > max_expand:
                return None
            fl = free[li]
            for di, dj, c in moves:
                ni, nj = i + di, j + dj
                if not (0 <= ni < H and 0 <= nj < W) or not fl[ni, nj]:
                    continue
                if di and dj and not (fl[i + di, j] and fl[i, j + dj]):
                    continue
                ng = gc + c * g * layer_cost[li]
                nxt = (li, ni, nj)
                if ng < best.get(nxt, 1e18) - 1e-9:
                    best[nxt] = ng
                    came[nxt] = cur
                    heapq.heappush(openh, (ng + hdist[ni, nj], ng, nxt))
            if freev[i, j]:
                ol = 1 - li
                if free[ol, i, j]:
                    ng = gc + vc
                    nxt = (ol, i, j)
                    if ng < best.get(nxt, 1e18) - 1e-9:
                        best[nxt] = ng
                        came[nxt] = cur
                        heapq.heappush(openh, (ng + hdist[i, j], ng, nxt))
        return None

    def _xy(self, i, j):
        return (round(self.x0 + (j + 0.5) * self.g, 4), round(self.y0 + (i + 0.5) * self.g, 4))

    def _commit(self, net, width, path):
        items = []
        runs = []
        cur = [path[0]]
        for p in path[1:]:
            if p[0] != cur[-1][0]:
                runs.append(cur)
                items.append(("via", self._xy(p[1], p[2])))
                cur = [p]
            else:
                cur.append(p)
        runs.append(cur)
        for run in runs:
            li = run[0][0]
            pts = [self._xy(i, j) for (_, i, j) in run]
            simp = [pts[0]]
            for k in range(1, len(pts) - 1):
                (ax, ay), (bx, by), (cx, cy) = simp[-1], pts[k], pts[k + 1]
                if abs((bx - ax) * (cy - by) - (by - ay) * (cx - bx)) > 1e-9:
                    simp.append(pts[k])
            if len(pts) > 1:
                simp.append(pts[-1])
            if len(simp) >= 2:
                items.append(("track", li, simp))
        lay = {0: pcbnew.F_Cu, 1: pcbnew.B_Cu}
        for it in items:
            if it[0] == "via":
                v = pcbnew.PCB_VIA(self.b)
                v.SetPosition(pcbnew.VECTOR2I(MM(it[1][0]), MM(it[1][1])))
                v.SetWidth(MM(self.via_d))
                v.SetDrill(MM(self.via_drill))
                v.SetNet(self.b.FindNet(net))
                self.b.Add(v)
                self._raster_track(v)
            else:
                _, li, pts = it
                for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
                    t = pcbnew.PCB_TRACK(self.b)
                    t.SetStart(pcbnew.VECTOR2I(MM(xa), MM(ya)))
                    t.SetEnd(pcbnew.VECTOR2I(MM(xb), MM(yb)))
                    t.SetWidth(MM(width))
                    t.SetLayer(lay[li])
                    t.SetNet(self.b.FindNet(net))
                    self.b.Add(t)
                    self._raster_track(t)
        return items

    # ------------------------------------------------------- stitching vias
    def stitch_pads(self, net, width=0.3, max_mm=2.5, layer=0):
        """Give every SMD pad of `net` on `layer` a short track to a via (for the other-layer pour)."""
        if net not in self.copper and "/" + net in self.copper:
            net = "/" + net
        added = 0
        free, freev = self._free_masks(net, width, (0, 1))
        for fp in self.b.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname() != net or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                    continue
                if not pad.IsOnLayer(LAYERS[layer]):
                    continue
                img = self._new_img()
                for pts in self._sps_points(pad.GetEffectivePolygon(LAYERS[layer], pcbnew.ERROR_INSIDE)):
                    self._poly_to(img, pts)
                pm = np.array(img, bool)
                start = pm & free[layer]
                if not start.any():
                    continue
                # BFS on the pad's layer out to max_mm for a legal via spot
                dist = ndimage.distance_transform_edt(~pm) * self.g
                cand = freev & (dist > 0) & (dist < max_mm) & free[layer] & free[1 - layer]
                if not cand.any():
                    continue
                ownm = np.stack([pm, np.zeros_like(pm)]) if layer == 0 else np.stack([np.zeros_like(pm), pm])
                tgt = np.stack([cand, np.zeros_like(cand)]) if layer == 0 else np.stack([np.zeros_like(cand), cand])
                path = self._astar(pm, ownm, tgt, free, np.zeros_like(freev), 1e9, (1.0, 1.0), 200_000)
                if path is None:
                    continue
                end = path[-1]
                self._commit(net, width, path)
                v = pcbnew.PCB_VIA(self.b)
                x, y = self._xy(end[1], end[2])
                v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
                v.SetWidth(MM(self.via_d))
                v.SetDrill(MM(self.via_drill))
                v.SetNet(self.b.FindNet(net))
                self.b.Add(v)
                self._raster_track(v)
                free, freev = self._free_masks(net, width, (0, 1))
                added += 1
        return added


def stitch_grid(router, net, pitch=4.0, margin=1.0):
    """Drop vias of `net` on a grid wherever legal (ties the top and bottom pours together)."""
    r = router
    if net not in r.copper and "/" + net in r.copper:
        net = "/" + net
    free, freev = r._free_masks(net, 0.3, (0, 1))
    n = 0
    step = max(1, int(round(pitch / r.g)))
    m = int(round(margin / r.g))
    for i in range(m, r.H - m, step):
        for j in range(m, r.W - m, step):
            if freev[i, j] and free[0, i, j] and free[1, i, j]:
                x, y = r._xy(i, j)
                v = pcbnew.PCB_VIA(r.b)
                v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
                v.SetWidth(MM(r.via_d))
                v.SetDrill(MM(r.via_drill))
                v.SetNet(r.b.FindNet(net))
                r.b.Add(v)
                r._raster_track(v)
                free, freev = r._free_masks(net, 0.3, (0, 1))
                n += 1
    return n
